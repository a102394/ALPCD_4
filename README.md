# ALPCD_4

**David José Silva e Costa** a102397	<br>
**Ioannis Nikolaos Kokkinovrachos** a106820 <br>	
**Joao Pedro Castro Magalhaes Alves** a102394	

## Passos para uso

### 1. **Clonar o Repositório**: 
Clone este repositório para sua máquina local utilizando o Git

Comando 1 - `git clone https://github.com/a102394/ALPCD_4.git`
Comando 2 - `cd ALPCD_4`

### 2. **Instalar as Dependências**: 
Instalar todas as bibliotecas necessárias para o funcionamento do projeto, conforme listadas no arquivo `requirements.txt`.

comando 3 -`pip install -r requirements.txt` 

Com essas duas etapas, o usuário conseguirá clonar o repositório e instalar as dependências do projeto de forma simples e direta.

## Comando disponíveis

### 1. Exibir ajuda com todos os comandos
Para exibir informações sobre os comandos disponíveis, execute o seguinte comando:
`python TP1.py help`
Esse comando irá exibir a lista completa de comandos e descrições de uso.

### 2. Mostrar as vagas mais recentes
Para mostrar as 'n' vagas mais recentes, execute o seguinte comando:
python TP1.py top <n> [--save]
<n>: Número de vagas a serem exibidas.
--save (opcional): Se fornecido, salva os resultados em um arquivo CSV chamado top_vagas.csv.

Exemplo:
`python TP1.py top 5 --save`
Este comando mostra as 5 vagas mais recentes e salva os resultados no arquivo top_vagas.csv.

### 3. Buscar vagas de uma empresa em uma localidade específica
Para procurar vagas para uma empresa específica em uma localidade específica, execute o seguinte comando:
python TP1.py search <empresa> <localidade> <n> [--save]
<empresa>: Nome da empresa.
<localidade>: Localidade para busca.
<n>: Número de vagas a serem exibidas.
--save (opcional): Se fornecido, salva os resultados em um arquivo CSV chamado search_vagas.csv.

Exemplo:
`python TP1.py search "altar.io" "Braga" 3 --save`
Este comando busca 3 vagas da empresa "altar.io" em "Braga" e salva os resultados no arquivo search_vagas.csv.

### 4. Exibir o salário de uma vaga pelo ID
Para exibir o salário de uma vaga específica, execute o seguinte comando:
python TP1.py salary <id>
<id>: ID da vaga.

Exemplo:
`python TP1.py salary 491881`
Este comando exibe o salário da vaga com o ID 491881.

### 5. Buscar vagas por habilidades dentro de um intervalo de datas
Para procurar vagas que exigem habilidades específicas dentro de um intervalo de datas, execute o seguinte comando:
python TP1.py skills <skills> <data_ini> <data_fim> [--save]
<skills>: Habilidades exigidas, separadas por vírgula.
<data_ini>: Data de início (formato YYYY-MM-DD).
<data_fim>: Data de término (formato YYYY-MM-DD).
--save (opcional): Se fornecido, salva os resultados em um arquivo CSV chamado skills_vagas.csv.

Exemplo:
`python TP1.py skills "Python, Data Science" "2024-01-01" "2024-12-31" --save`
Este comando busca vagas que exigem as habilidades "Python" e "Data Science" no intervalo de 01/01/2024 a 31/12/2024 e salva os resultados no arquivo skills_vagas.csv.

### 6. Forçar o recarregamento dos dados da API
Para forçar o recarregamento dos dados da API, ignorando o cache, execute o seguinte comando:
`python TP1.py reloadapi`
Este comando atualiza o cache com os dados mais recentes da API.
