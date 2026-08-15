<p align="center">
  <img src="caramelo.jpeg" alt="Caramelo Storm" width="160">
</p>

<h1 align="center">BH_AdjustTrust</h1>

<p align="center">
  <strong>Corrige campos de Trust do BloodHound CE para importação de collectors.</strong><br>
  Converte valores numéricos (TrustDirection, TrustType, TrustAttributes) para strings
  no formato esperado pelo CE.
</p>

<p align="center">
  <em>Feito por <strong>Avocado</strong> · equipe <strong>Caramelo Storm</strong></em><br>
  <a href="https://www.linkedin.com/in/rafael-raugi/">💼 LinkedIn</a> ·
  <a href="https://www.youtube.com/@avocado-shell">📺 YouTube @avocado-shell</a>
</p>

---

Ao coletar dados de Active Directory com **nxc** ou **bloodhound-python**, os campos de
confiança (Trusts) são armazenados como numeros (valores crus do LDAP). O BloodHound CE,
porém, espera esses campos como strings. Na tentativa de importar, você vê:

```
Error: cannot unmarshal number into Go struct field ... of type string
```

O `BH_AdjustTrust` resolve isso: lê o `*_domains.json` coletado, converte os campos
numericos para o formato correto e gera um arquivo `-fixed.json` pronto para importar.

## O que ele faz

- **Converte TrustDirection** — `0` → `"Disabled"`, `1` → `"Inbound"`, `2` → `"Outbound"`,
  `3` → `"Bidirectional"`.
- **Infere TrustType** — a partir dos atributos do trust (se presente) ou do parentesco
  entre os nomes DNS: `"ParentChild"`, `"Forest"` ou `"External"`.
- **Stringify TrustAttributes** — preserva o valor numerico mas como string (`"0x20"` etc).
- **Saída limpa** — um arquivo JSON valido, mesma estrutura, só com os tipos certos.

## Como rodar

```bash
cd BH_AdjustTrust
./BH_AdjustTrust.py <arquivo_domains.json>
```

Gera um arquivo `<arquivo_domains>-fixed.json` que pode ser importado normalmente
no BloodHound CE sem erros de tipo.

## Exemplo

```bash
./BH_AdjustTrust.py acme_domains.json
```

Saida esperada:

```
[+] ACME.COM -> child.acme.com: TrustDirection 1 -> "Inbound", TrustType 2 -> "Forest"
[+] CORP.INT -> ACME.COM: TrustDirection 2 -> "Outbound", TrustType 2 -> "Forest"
[*] 2 trust(s) corrigido(s)
[*] gravado: acme_domains-fixed.json
```

Se o arquivo ja está correto (sem campos numericos), o script avisa:

```
[*] nenhum campo numerico encontrado (arquivo ja estava ok)
[*] gravado: acme_domains-fixed.json
```

## Requisitos

- **Python 3.6+** (stdlib apenas — **sem dependências externas**)

## Como funciona (resumo)

1. Lê o JSON do collector (nxc ou bloodhound-python).
2. Para cada dominio e seu trust:
   - Se `TrustDirection` for numero: converte via tabela LDAP → string BloodHound.
   - Se `TrustType` for numero: infere a partir dos `TrustAttributes` ou nomes DNS.
   - Se `TrustAttributes` for numero: converte para string.
3. Escreve o JSON corrigido em `<arquivo>-fixed.json`.
4. Imprime um relatorio das mudancas.

## Estrutura

```
BH_AdjustTrust.py     o corrector (Python 3, stdlib, sem dependências)
README.md             esta documentacao
LICENSE               MIT
.gitignore            excluir artefatos temporarios
caramelo.jpeg         logo da equipe
```

## Uso em pipelines

```bash
# Coletar com nxc
bloodhound-python -d ACME.COM -u usuario -p senha -ns 192.168.1.10 -c All

# Corrigir
python BH_AdjustTrust.py ACME.COM_domains.json

# Importar no BloodHound CE
# (use a versão -fixed.json)
```

## Aviso

Ferramenta de apoio a **operações ofensivas autorizadas**. Os dados coletados (estrutura
do Active Directory do cliente) só devem ser usados dentro do escopo de uma **autorização
por escrito**. Você é responsável pelo uso.

## Licença

[MIT](LICENSE) — uso autorizado apenas em assessments com autorização por escrito.

---

<p align="center">
  <sub>⚡ <strong>Caramelo Storm</strong> ·
  <a href="https://www.linkedin.com/in/rafael-raugi/">LinkedIn</a> ·
  <a href="https://www.youtube.com/@avocado-shell">YouTube @avocado-shell</a></sub>
</p>
