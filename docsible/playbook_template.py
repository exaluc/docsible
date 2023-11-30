static_playbook = """{{- role.existing_readme -}}

# Generated with docsible {{ role.dt_generated }}
{% if role.playbook.content -%}
## Playbook
```yml
{{ role.playbook.content }}
```
{%- endif %}
{% if role.playbook.graph -%}
## Playbook graph
```mermaid
{{ role.playbook.graph }}
```
{%- endif %}

"""