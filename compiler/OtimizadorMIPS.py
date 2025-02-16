import re
from collections import defaultdict

class OtimizadorMIPS:
    def __init__(self):
        self.valores_registradores = {}
        self.registradores_usados = set()
        self.rotulos = set()
        self.referencias_rotulos = defaultdict(int)
        self.alvos_salto = set()
        self.funcoes = set()  
        
    def analisar_instrucao(self, linha):
        """Analisa uma instrução em seus componentes"""
        linha = linha.strip()
        if not linha or linha.startswith('#'):
            return None
            
        if linha.startswith('.'):
            return {'tipo': 'diretiva', 'original': linha}
            
        if ':' in linha:
            rotulo = linha.split(':')[0].strip()
            self.rotulos.add(rotulo)
            if '.' in rotulo: 
                self.funcoes.add(rotulo)
            return {'tipo': 'rotulo', 'rotulo': rotulo}
            
        linha = linha.split('#')[0].strip()
        if not linha:
            return None
            
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
        
        self.analisar_programa(instrucoes)
        
        instrucoes = self.remover_codigo_morto(instrucoes)
        instrucoes = self.dobramento_constantes(instrucoes)
        instrucoes = self.reducao_forca(instrucoes)
        instrucoes = self.remover_operacoes_redundantes(instrucoes)
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
                if '.' in parsed['rotulo']:  
                    self.funcoes.add(parsed['rotulo'])
            elif parsed['tipo'] == 'instrucao':
                op = parsed['op']
                args = parsed['args']
                
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
                
            if parsed['tipo'] == 'diretiva':
                codigo_vivo.append(instr)
                continue
                
            if parsed['tipo'] == 'rotulo':
                rotulo = parsed['rotulo']
                if rotulo in self.funcoes or rotulo == 'main':
                    em_funcao = True
                    funcao_atual = rotulo
                codigo_vivo.append(instr)
                continue
                
            if em_funcao or parsed['tipo'] == 'instrucao' and parsed['op'] in ['jal', 'jr', 'syscall']:
                codigo_vivo.append(instr)
                if parsed['op'] == 'jr' and parsed['args'][0] == '$ra':
                    em_funcao = False
                    funcao_atual = None
                
        return codigo_vivo

    def remover_operacoes_redundantes(self, instrucoes):
        """Remove operações redundantes como multiplicação por 1 e adição com 0"""
        otimizado = []
        i = 0
        
        while i < len(instrucoes):
            if i + 2 >= len(instrucoes):  # Se não houver instruções suficientes para formar o padrão
                otimizado.append(instrucoes[i])
                i += 1
                continue
                
            instr1 = self.analisar_instrucao(instrucoes[i])
            instr2 = self.analisar_instrucao(instrucoes[i+1])
            instr3 = self.analisar_instrucao(instrucoes[i+2])
            
            # Se alguma das instruções não for válida, continue normalmente
            if not instr1 or not instr2 or not instr3:
                otimizado.append(instrucoes[i])
                i += 1
                continue
                
            # Verifica se é um padrão de multiplicação por 1
            if (instr1['tipo'] == 'instrucao' and instr1['op'] == 'li' and
                instr2['tipo'] == 'instrucao' and instr2['op'] == 'lw' and
                instr3['tipo'] == 'instrucao' and instr3['op'] == 'mul'):
                
                # Verifica se está carregando 1 e multiplicando pelo valor carregado
                if (len(instr1['args']) == 2 and instr1['args'][1] == '1' and
                    len(instr3['args']) == 3 and
                    (instr3['args'][2] == instr1['args'][0] or instr3['args'][1] == instr1['args'][0])):
                    
                    # Mantém apenas o lw, ajustando o registrador de destino
                    novo_lw = f"lw {instr3['args'][0]}, {instr2['args'][1]}"
                    otimizado.append(novo_lw)
                    i += 3
                    continue
                    
            # Verifica se é um padrão de adição com 0
            if (instr1['tipo'] == 'instrucao' and instr1['op'] == 'li' and
                instr2['tipo'] == 'instrucao' and instr2['op'] == 'lw' and
                instr3['tipo'] == 'instrucao' and instr3['op'] == 'add'):
                
                # Verifica se está carregando 0 e somando com o valor carregado
                if (len(instr1['args']) == 2 and instr1['args'][1] == '0' and
                    len(instr3['args']) == 3 and
                    (instr3['args'][2] == instr1['args'][0] or instr3['args'][1] == instr1['args'][0])):
                    
                    # Mantém apenas o lw, ajustando o registrador de destino
                    novo_lw = f"lw {instr3['args'][0]}, {instr2['args'][1]}"
                    otimizado.append(novo_lw)
                    i += 3
                    continue
            
            otimizado.append(instrucoes[i])
            i += 1
            
        return otimizado    
    
    def dobramento_constantes(self, instrucoes):
        """Realiza dobramento de constantes"""
        otimizado = []
        self.valores_registradores.clear()
        
        for instr in instrucoes:
            parsed = self.analisar_instrucao(instr)
            if not parsed or parsed['tipo'] != 'instrucao':
                otimizado.append(instr)
                continue
                
            if parsed['op'] == 'li' and len(parsed['args']) == 2:
                try:
                    valor = int(parsed['args'][1])
                    self.valores_registradores[parsed['args'][0]] = valor
                except ValueError:
                    pass
                    
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
            
            if op == 'mul' and len(args) == 3:
                try:
                    value = int(args[2])
                    if value > 0 and (value & (value - 1)) == 0: 
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