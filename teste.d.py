import requests
import math
import json
import os
import typer
import csv
from time import sleep
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

app = typer.Typer()

# Variáveis globais
BASE_URL = "https://www.glassdoor.com/Job/vienna-austria-data-scientist-jobs-SRCH_IL.0,14_IC3174503_KO15,29.htm"
CACHE_FILE = "cache_vagas.json"
general_results = []

def echo_verde(msg: str):
    """Exibe uma mensagem em verde."""
    typer.echo(typer.style(msg, fg=typer.colors.GREEN))

def echo_vermelho(msg: str):
    """Exibe uma mensagem em vermelho."""
    typer.echo(typer.style(msg, fg=typer.colors.RED))

def save_to_csv(data, filename):
    """Salva os dados em um arquivo CSV."""
    keys = ['job_title', 'company', 'location']
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        for item in data:
            writer.writerow(item)
    echo_verde(f"Arquivo CSV '{filename}' salvo com sucesso.")

def load_cache():
    """Carrega o cache do arquivo, se existir."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        echo_vermelho("Arquivo de cache não encontrado.")
        return []

def fetch_from_html():
    """Busca vagas diretamente do HTML do Glassdoor e retorna os dados."""
    try:
        response = requests.get(BASE_URL, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        jobs = []
        job_cards = soup.find_all('li', class_='react-job-listing')
        for card in job_cards:
            title = card.find('a', class_='jobLink').text.strip() if card.find('a', class_='jobLink') else "N/A"
            company = card.find('div', class_='jobHeader').text.strip() if card.find('div', class_='jobHeader') else "N/A"
            location = card.find('span', class_='loc').text.strip() if card.find('span', class_='loc') else "N/A"
            jobs.append({
                'job_title': title,
                'company': company,
                'location': location
            })

        with open(CACHE_FILE, 'w', encoding='utf-8') as file:
            json.dump(jobs, file, ensure_ascii=False, indent=4)
        echo_verde(f"Cache salvo no arquivo '{CACHE_FILE}'.")
        return jobs

    except requests.RequestException as e:
        echo_vermelho(f"Erro ao acessar o Glassdoor: {e}")
        return []

def getdata(force_reload: bool = False):
    """Obtém dados das vagas. Usa cache, a menos que force_reload seja True."""
    global general_results
    if force_reload:
        echo_verde("Carregando dados do Glassdoor...")
        general_results = fetch_from_html()
    else:
        general_results = load_cache()
    return general_results

@app.command()
def statistics(group_by: str):
    """Gera estatísticas de vagas agrupadas por zona ou tipo de trabalho."""
    general_results = getdata()
    grouped_data = {}

    if group_by == "zone":
        for job in general_results:
            location = job.get('location', 'Unknown')
            if location not in grouped_data:
                grouped_data[location] = []
            grouped_data[location].append(job)

        save_to_csv(general_results, "statistics_zone.csv")
        echo_verde(f"Estatísticas por zona salvas em 'statistics_zone.csv'.")

    else:
        echo_vermelho("Opção de agrupamento inválida. Use 'zone'.")

@app.command()
def list_jobs():
    """Lista todas as vagas salvas no cache."""
    general_results = getdata()
    if not general_results:
        echo_vermelho("Nenhuma vaga encontrada.")
        return

    for job in general_results:
        typer.echo(f"{job['job_title']} - {job['company']} ({job['location']})")

@app.command()
def reload_data():
    """Força o recarregamento dos dados diretamente do Glassdoor."""
    getdata(force_reload=True)

if __name__ == "__main__":
    app()
