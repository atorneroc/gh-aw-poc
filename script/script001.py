import requests
import time
import pandas as pd

# Configuración de la organización y tema
ORG = "CCAPITAL-APPS"
TOPIC = "tribu-canal-digital"

# Configuración de Sharding
SHARDS = 20
SHARD_ID = 1  # Define el shard actual
OUT_FILE = f"prs_merged_main_shard_{SHARD_ID}_of_{SHARDS}_PBI_110326.csv"

# Reemplaza estos valores con los tuyos
TOKEN = "token_github"  # Reemplaza con tu token de GitHub
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# Función para hacer la solicitud GET y manejar errores y límites de tasa
def get(url):
    while True:
        response = requests.get(url, headers=HEADERS)
        
        # Si el límite de tasa se ha alcanzado, esperar hasta que se restablezca
        if response.status_code == 403:  # Código de error para límites de tasa
            remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
            
            if remaining == 0:
                reset_time_unix = time.gmtime(reset_time)
                print(f"Límite de tasa alcanzado. Esperando hasta {time.strftime('%Y-%m-%d %H:%M:%S', reset_time_unix)}...")
                # Esperar hasta que se restablezca el límite
                time_to_wait = reset_time - time.time()
                if time_to_wait > 0:
                    time.sleep(time_to_wait)
                continue  # Reintentar la solicitud después de la espera
        
        if response.status_code == 200:
            return response.json()  # Convertir la respuesta en un objeto JSON
        else:
            print(f"Error {response.status_code}: No se pudieron obtener los datos desde {url}")
            return None

# Función para obtener los repositorios de la organización filtrados por un tema
def get_repos_by_topic(org, topic):
    repos = []
    page = 1  # Página inicial
    while True:
        url = f"https://api.github.com/orgs/{org}/repos?per_page=100&page={page}"  # Añadido 'page' y 'per_page'
        response = get(url)
        if not response:  # Si la respuesta es vacía, significa que no hay más repos
            break
        repos_page = response  # La respuesta ya es un diccionario JSON
        
        if not repos_page:  # Si no hay repos en la página, detener el ciclo
            break
        
        # Filtramos los repos por el tema
        filtered_repos = [repo for repo in repos_page if topic in repo.get('topics', [])]
        repos.extend(filtered_repos)  # Agregar repos de esta página
        print(f"Página {page} obtenida. Total de repos: {len(repos)}")
        page += 1  # Ir a la siguiente página
    
    print(f"Repos filtrados por el tema '{topic}'")
    return repos

# Función para obtener los PRs de manera paginada
def get_all_prs(repo_owner, repo_name, base_branch, head_branch):
    prs = []
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls?base={base_branch}&head={head_branch}&state=closed"
    
    while url:
        response = get(url)
        if isinstance(response, list):  # Si la respuesta es una lista, no hay más páginas
            prs.extend(response)  # Agregar PRs a la lista
            break  # Salir del ciclo porque no hay paginación adicional
        # Si no es una lista, verificamos si hay paginación
        elif 'link' in response.headers and 'rel="next"' in response.headers['link']:
            next_url = response.headers['link'].split(",")[1].split(";")[0].strip()[1:-1]
            url = next_url  # Asignar la siguiente URL de la paginación
        else:
            url = None  # No hay más páginas
    return prs

# Función para obtener los commits de un PR
def get_commits_from_pull(pr_number, repo_owner, repo_name):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/commits"
    return get(url)

# Paso 1: Obtener los repositorios con el tema 'tribu-canal-digital'
repos = get_repos_by_topic(ORG, TOPIC)

# Paso 2: Para cada repositorio, obtener los commits verificados, PRs y exportar los resultados
commits_info = []

# Determinar el rango de repos a procesar según el sharding
total_repos = len(repos)
repos_per_shard = total_repos // SHARDS
repos_to_process = repos[(SHARD_ID - 1) * repos_per_shard: SHARD_ID * repos_per_shard]

# Procesar cada repositorio
for repo in repos_to_process:
    repo_name = repo['name']
    print(f"Procesando repositorio: {repo_name}")

    # Obtener los PRs realizados a la rama `develop`
    develop_prs = get_all_prs(ORG, repo_name, "develop", "")
    
    # Paso 2.1: Recorrer los commits de cada PR de develop y obtener la información relevante
    for pr in develop_prs:
        pr_commits = get_commits_from_pull(pr['number'], ORG, repo_name)
        for commit in pr_commits:
            commit_sha = commit['sha']
            commit_date = commit['commit']['author']['date']
            pr_id = pr['number']
            merged_at = pr.get('merged_at', None)
            source_branch = pr['head']['ref']  # Rama que hizo el pull
            commits_info.append({
                "repo_name": repo_name,  # Nombre del repositorio agregado al inicio
                "commit_sha": commit_sha,
                "commit_date": commit_date,
                "pr_id": pr_id,
                "merged_at": merged_at,
                "source_branch": source_branch
            })

    # Paso 3: Obtener los PRs de `develop` a `qa`
    qa_prs = get_all_prs(ORG, repo_name, "qa", "develop")
    
    # Paso 4: Verificar los commits de `develop` en los PRs de `qa`
    for pr in qa_prs:
        pr_commits = get_commits_from_pull(pr['number'], ORG, repo_name)
        for commit in pr_commits:
            commit_sha = commit['sha']
            for info in commits_info:
                if info['commit_sha'] == commit_sha:
                    info['pr_dev_qa_id'] = pr['number']
                    info['merge_to_qa_date'] = pr.get('merged_at', None)

    # Paso 5: Obtener los PRs de `qa` a `main`
    main_prs = get_all_prs(ORG, repo_name, "main", "qa")
    
    # Paso 6: Verificar los commits de `qa` en los PRs de `main`
    for pr in main_prs:
        pr_commits = get_commits_from_pull(pr['number'], ORG, repo_name)
        for commit in pr_commits:
            commit_sha = commit['sha']
            for info in commits_info:
                if info['commit_sha'] == commit_sha:
                    info['pr_qa_main_id'] = pr['number']
                    info['merge_to_main_date'] = pr.get('merged_at', None)

# Paso 7: Crear un DataFrame y exportarlo a CSV
df = pd.DataFrame(commits_info, columns=["repo_name", "commit_sha", "commit_date", "pr_id", "merged_at", "source_branch", "pr_dev_qa_id", "merge_to_qa_date", "pr_qa_main_id", "merge_to_main_date"])

# Exportar los resultados a un archivo CSV
df.to_csv(OUT_FILE, index=False)
print(f"Exportados {len(df)} commits a {OUT_FILE}")
