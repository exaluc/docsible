# Import libraries
import os
import yaml
import click
from shutil import copyfile
from datetime import datetime
from jinja2 import Environment, BaseLoader
from role_template import static_template
from playbook_template import static_playbook
from utils.mermaid import generate_mermaid_playbook, generate_mermaid_role_tasks_per_file
from utils.yaml import load_yaml_generic, load_yaml_files_from_dir_custom
from utils.special_tasks_keys import process_special_task_keys

def get_version():
    return "0.4.12"

# Constants for default file paths and settings
DEFAULT_PLAYBOOK = './tests/test.yml'
DOCSIBLE_FILE_NAME = '.docsible'

# Initialize the Jinja2 Environment
env = Environment(loader=BaseLoader)

timestamp_readme = datetime.now().strftime('%d/%m/%Y')

def initialize_docsible(docsible_path, default_data):
    try:
        with open(docsible_path, 'w') as f:
            yaml.dump(default_data, f, default_flow_style=False)
        print(f"Initialized {docsible_path} with default keys.")
    except Exception as e:
        print(f"An error occurred while initializing {docsible_path}: {e}")


def backup_file(file_path):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    backup_path = f"{file_path}_backup_{timestamp}"
    copyfile(file_path, backup_path)
    print(f'File backed up as: {backup_path}')

def generate_documentation(readme_path, playbook_info, generate_graph):
    mermaid_code_per_file = {}
    if generate_graph and 'playbook' in playbook_info and playbook_info['playbook']['graph']:
        mermaid_code_per_file = {'playbook_graph': playbook_info['playbook']['graph']}

    template = env.from_string(static_playbook)
    output = template.render(role=playbook_info, mermaid_code_per_file=mermaid_code_per_file)

    with open(readme_path, "w") as f:
        f.write(output)
    print('Documentation generated at:', readme_path)

@click.command()
@click.option('--role', default='.', help='Path to the Ansible role directory.')
@click.option('--playbook', default=DEFAULT_PLAYBOOK, help='Path to the playbook file.')
@click.option('--merge-md', is_flag=True, help='Merge existing readme (works only for playbook)')
@click.option('--only-play', is_flag=True, help='Generate doc only for playbook.')
@click.option('--graph', is_flag=True, help='Generate Mermaid graph for tasks.')
@click.option('--no-backup', is_flag=True, help='Don\'t backup the readme before remove.')
@click.version_option(version=get_version(), help="Show the module version.")
def doc_the_role(role, playbook, graph, no_backup, only_play, merge_md):
    if only_play:
        handle_playbook_only(playbook, no_backup, merge_md)
        return

    document_role(role, playbook, graph, no_backup)

def load_playbook_content(playbook_path):
    try:
        with open(playbook_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print('Playbook not found:', playbook_path)
    except Exception as e:
        print('Playbook import error:', e)
    return None

def handle_playbook_only(playbook, no_backup, merge_md):
    playbook_content = load_playbook_content(playbook)
    if playbook_content is None:
        return

    playbook_dir = os.path.dirname(os.path.abspath(playbook))
    readme_path = os.path.join(playbook_dir, "README.md")

    # Check if README exists and read its content
    existing_readme_content = ""
    if os.path.exists(readme_path):
        if merge_md:
            with open(readme_path, 'r') as file:
                existing_readme_content = file.read()
        if not no_backup:
            backup_file(readme_path)

    playbook_info = {
        "name": os.path.basename(playbook_dir),
        "existing_readme": existing_readme_content,
        "dt_generated": timestamp_readme,
        "playbook": {
            "content": playbook_content,
            "graph": generate_mermaid_playbook(yaml.safe_load(playbook_content)) if playbook_content else None
        }
    }

    generate_documentation(readme_path, playbook_info, True)

def document_role(role_path, playbook_content, generate_graph, no_backup):
    role_name = os.path.basename(role_path)
    readme_path = os.path.join(role_path, "README.md")
    meta_path = os.path.join(role_path, "meta", "main.yml")

    defaults_data = load_yaml_files_from_dir_custom(
        os.path.join(role_path, "defaults")) or []
    vars_data = load_yaml_files_from_dir_custom(
        os.path.join(role_path, "vars")) or []
    docsible_path = os.path.join(role_path, DOCSIBLE_FILE_NAME)

    if os.path.exists(docsible_path):
        docsible_present = True
    else:
        default_data = {
            'description': None,
            'requester': None,
            'users': None,
            'dt_dev': None,
            'dt_prod': None,
            'dt_update': timestamp_readme,
            'version': None,
            'time_saving': None,
            'category': None,
            'subCategory': None,
            'aap_hub': None
        }

        if not os.path.exists(docsible_path):
            print(f"{docsible_path} not found. Initializing...")
            try:
                initialize_docsible(docsible_path, default_data)
                docsible_present = True
            except Exception as e:
                print(
                    f"An error occurred while initializing {docsible_path}: {e}")

    role_info = {
        "name": role_name,
        "defaults": defaults_data,
        "vars": vars_data,
        "tasks": [],
        "meta": load_yaml_generic(meta_path) or {},
        "playbook": {"content": playbook_content, "graph": generate_mermaid_playbook(yaml.safe_load(playbook_content)) if playbook_content else None},
        "docsible": load_yaml_generic(docsible_path) if docsible_present else None
    }

    tasks_dir = os.path.join(role_path, "tasks")
    role_info["tasks"] = []

    if os.path.exists(tasks_dir) and os.path.isdir(tasks_dir):
        for dirpath, dirnames, filenames in os.walk(tasks_dir):
            for task_file in filenames:
                if task_file.endswith(".yml"):
                    file_path = os.path.join(dirpath, task_file)
                    tasks_data = load_yaml_generic(file_path)
                    if tasks_data:
                        relative_path = os.path.relpath(file_path, tasks_dir)
                        task_info = {'file': relative_path, 'tasks': [], 'mermaid': []}
                        if not isinstance(tasks_data, list):
                            print(
                                f"Unexpected data type for tasks in {task_file}. Skipping.")
                            continue
                        for task in tasks_data:
                            if not isinstance(task, dict):
                                print(
                                    f"Skipping unexpected data in {task_file}: {task}")
                                continue
                            if task and len(task.keys()) > 0:
                                processed_tasks = process_special_task_keys(task)
                                task_info['tasks'].extend(processed_tasks)
                                task_info['mermaid'].extend([task])
                        role_info["tasks"].append(task_info)

    if os.path.exists(readme_path):
        if not no_backup:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            backup_readme_path = os.path.join(role_path, f"README_backup_{timestamp}.md")
            copyfile(readme_path, backup_readme_path)
            print(f'Readme file backed up as: {backup_readme_path}')
        os.remove(readme_path)

    role_info["existing_readme"] = ""

    mermaid_code_per_file = {}
    if generate_graph:
        mermaid_code_per_file = generate_mermaid_role_tasks_per_file(
            role_info["tasks"])

    # Render the static template
    template = env.from_string(static_template)
    output = template.render(
        role=role_info, mermaid_code_per_file=mermaid_code_per_file)

    with open(readme_path, "w") as f:
        f.write(output)

    print('Documentation generated at:', readme_path)


if __name__ == '__main__':
    doc_the_role()
