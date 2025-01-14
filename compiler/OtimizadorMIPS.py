import re
from collections import defaultdict

class OtimizadorMIPS:
    def __init__(self):
        self.valores_registradores = {}
        self.registradores_usados = set()
        self.rotulos = set()
        self.referencias_rotulos = defaultdict(int)
        self.alvos_salto = set()
        self.funcoes = set()  # Track function labels
        
    def analisar_instrucao(self, linha):
        """Analisa uma instrução em seus componentes"""
        linha = linha.strip()
        if not linha or linha.startswith('#'):
            return None
            
        # Preserve directives
        if linha.startswith('.'):
            return {'tipo': 'diretiva', 'original': linha}
            
        # Handle labels
        if ':' in linha:
            rotulo = linha.split(':')[0].strip()
            self.rotulos.add(rotulo)
            if '.' in rotulo:  # Function labels like Fac.ComputeFac
                self.funcoes.add(rotulo)
            return {'tipo': 'rotulo', 'rotulo': rotulo}
            
        # Remove comments
        linha = linha.split('#')[0].strip()
        if not linha:
            return None
            
        # Parse instruction
        partes = re.split(r'[\s,]+', linha)
        return {
            'tipo': 'instrucao',
            'op': partes[0],
            'args': partes[1:],
            'original': linha
        }

    def otimizar(self, codigo):
        """Aplica otimizações preservando a semântica do programa"""
        instrucoes = codigo.split('\n')
        
        # Build initial analysis
        self.analisar_programa(instrucoes)
        
        # Apply safe optimizations
        instrucoes = self.remover_codigo_morto(instrucoes)
        instrucoes = self.dobramento_constantes(instrucoes)
        instrucoes = self.reducao_forca(instrucoes)
        instrucoes = self.remover_movimentacoes_redundantes(instrucoes)
        instrucoes = self.remover_instrucoes_nop(instrucoes)
        
        return '\n'.join(filter(None, instrucoes))

    def analisar_programa(self, instrucoes):
        """Analisa estrutura do programa para identificar funções e fluxo de controle"""
        self.rotulos.clear()
        self.referencias_rotulos.clear()
        self.alvos_salto.clear()
        self.funcoes.clear()
        
        for instr in instrucoes:
            parsed = self.analisar_instrucao(instr)
            if not parsed:
                continue
                
            if parsed['tipo'] == 'rotulo':
                if '.' in parsed['rotulo']:  # Function labels
                    self.funcoes.add(parsed['rotulo'])
            elif parsed['tipo'] == 'instrucao':
                op = parsed['op']
                args = parsed['args']
                
                # Track jumps and branches
                if op in ['j', 'jal', 'beq', 'bne', 'beqz', 'bnez']:
                    if len(args) > 0:
                        target = args[-1]
                        self.referencias_rotulos[target] += 1
                        self.alvos_salto.add(target)

    def remover_codigo_morto(self, instrucoes):
        """Remove código morto preservando funções e fluxo de controle"""
        codigo_vivo = []
        em_funcao = False
        funcao_atual = None
        
        for instr in instrucoes:
            parsed = self.analisar_instrucao(instr)
            if not parsed:
                codigo_vivo.append(instr)
                continue
                
            # Always keep directives
            if parsed['tipo'] == 'diretiva':
                codigo_vivo.append(instr)
                continue
                
            # Handle labels
            if parsed['tipo'] == 'rotulo':
                rotulo = parsed['rotulo']
                if rotulo in self.funcoes or rotulo == 'main':
                    em_funcao = True
                    funcao_atual = rotulo
                codigo_vivo.append(instr)
                continue
                
            # Keep all instructions in functions and main
            if em_funcao or parsed['tipo'] == 'instrucao' and parsed['op'] in ['jal', 'jr', 'syscall']:
                codigo_vivo.append(instr)
                if parsed['op'] == 'jr' and parsed['args'][0] == '$ra':
                    em_funcao = False
                    funcao_atual = None
                
        return codigo_vivo

    def dobramento_constantes(self, instrucoes):
        """Realiza dobramento de constantes de forma segura"""
        otimizado = []
        self.valores_registradores.clear()
        
        for instr in instrucoes:
            parsed = self.analisar_instrucao(instr)
            if not parsed or parsed['tipo'] != 'instrucao':
                otimizado.append(instr)
                continue
                
            # Only optimize simple arithmetic with immediates
            if parsed['op'] == 'li' and len(parsed['args']) == 2:
                try:
                    valor = int(parsed['args'][1])
                    self.valores_registradores[parsed['args'][0]] = valor
                except ValueError:
                    pass
                    
            # Clear register value on modification
            if len(parsed['args']) > 0:
                self.valores_registradores.pop(parsed['args'][0], None)
                
            otimizado.append(instr)
            
        return otimizado

    def reducao_forca(self, instrucoes):
        """Aplica redução de força em operações aritméticas"""
        otimizado = []
        
        for instr in instrucoes:
            parsed = self.analisar_instrucao(instr)
            if not parsed or parsed['tipo'] != 'instrucao':
                otimizado.append(instr)
                continue
                
            op = parsed['op']
            args = parsed['args']
            
            # Optimize multiplication by powers of 2
            if op == 'mul' and len(args) == 3:
                try:
                    value = int(args[2])
                    if value > 0 and (value & (value - 1)) == 0:  # Is power of 2
                        shift = value.bit_length() - 1
                        otimizado.append(f"sll {args[0]}, {args[1]}, {shift}")
                        continue
                except ValueError:
                    pass
                    
            otimizado.append(instr)
            
        return otimizado

    def remover_movimentacoes_redundantes(self, instrucoes):
        """Remove movimentações redundantes preservando contexto"""
        otimizado = []
        
        for instr in instrucoes:
            parsed = self.analisar_instrucao(instr)
            if not parsed or parsed['tipo'] != 'instrucao':
                otimizado.append(instr)
                continue
                
            # Only remove obvious redundant moves
            if parsed['op'] == 'move' and len(parsed['args']) == 2:
                if parsed['args'][0] == parsed['args'][1]:
                    continue
                    
            otimizado.append(instr)
            
        return otimizado

    def remover_instrucoes_nop(self, instrucoes):
        """Remove instruções sem efeito preservando estrutura do programa"""
        otimizado = []
        
        for instr in instrucoes:
            parsed = self.analisar_instrucao(instr)
            if not parsed or parsed['tipo'] != 'instrucao':
                otimizado.append(instr)
                continue
                
            op = parsed['op']
            args = parsed['args']
            
            # Only remove obvious no-op instructions
            if op == 'add' and len(args) == 3 and args[2] == '$zero' and args[0] == args[1]:
                continue
            if op == 'sub' and len(args) == 3 and args[2] == '$zero' and args[0] == args[1]:
                continue
                
            otimizado.append(instr)
            
        return otimizado

def main():
    with open('output_code.txt', 'r') as f:
        codigo = f.read()

    otimizador = OtimizadorMIPS()
    codigo_otimizado = otimizador.otimizar(codigo)
    
    print("Código MIPS Otimizado:")
    print(codigo_otimizado)
    
    with open('codigo_otimizado.txt', 'w') as f:
        f.write(codigo_otimizado)

if __name__ == "__main__":
    main()