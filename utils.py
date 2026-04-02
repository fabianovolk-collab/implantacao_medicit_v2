import re

def somente_numeros(valor):
    return re.sub(r"\D", "", str(valor))

def validar_cpf(cpf):
    cpf = somente_numeros(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    dig1 = (soma * 10 % 11) % 10
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    dig2 = (soma * 10 % 11) % 10
    return cpf[-2:] == f"{dig1}{dig2}"

def validar_cnpj(cnpj):
    cnpj = somente_numeros(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    def calc(cnpj, pesos):
        soma = sum(int(cnpj[i]) * pesos[i] for i in range(len(pesos)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto
    pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    pesos2 = [6] + pesos1
    dig1 = calc(cnpj, pesos1)
    dig2 = calc(cnpj + str(dig1), pesos2)
    return cnpj[-2:] == f"{dig1}{dig2}"

def validar_documento(doc):
    doc = somente_numeros(doc)
    if len(doc) == 11:
        return validar_cpf(doc)
    elif len(doc) == 14:
        return validar_cnpj(doc)
    return False

def validar_documento_tempo_real(doc):
    doc = somente_numeros(doc)
    if not doc:
        return None, ""
    if len(doc) < 11:
        return False, "Documento incompleto"
    if len(doc) == 11:
        return (True, "CPF válido") if validar_cpf(doc) else (False, "CPF inválido")
    if len(doc) == 14:
        return (True, "CNPJ válido") if validar_cnpj(doc) else (False, "CNPJ inválido")
    return False, "Documento inválido"

def formatar_telefone(valor):
    valor = somente_numeros(valor)
    if len(valor) > 10:
        return f"({valor[:2]}) {valor[2]} {valor[3:7]}-{valor[7:11]}"
    elif len(valor) > 6:
        return f"({valor[:2]}) {valor[2:6]}-{valor[6:]}"
    elif len(valor) > 2:
        return f"({valor[:2]}) {valor[2:]}"
    return valor

def formatar_cnpj_cpf(numero):
    numero = somente_numeros(str(numero))
    if len(numero) == 11:
        return f"{numero[:3]}.{numero[3:6]}.{numero[6:9]}-{numero[9:]}"
    elif len(numero) == 14:
        return f"{numero[:2]}.{numero[2:5]}.{numero[5:8]}/{numero[8:12]}-{numero[12:]}"
    return numero
