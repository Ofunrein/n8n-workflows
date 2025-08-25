#!/usr/bin/env python3
"""
Build lightweight workflow data for Vercel deployment.
Processes all workflow files and creates a JSON file that can be deployed to Vercel.
"""

import json
import os
from pathlib import Path
import hashlib
from typing import Dict, List, Any, Optional

def get_file_hash(file_path: str) -> str:
    """Get MD5 hash of file for change detection."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except:
        return ""

def format_workflow_name(filename: str) -> str:
    """Convert filename to readable workflow name."""
    name = filename.replace('.json', '')
    parts = name.split('_')
    if len(parts) > 1 and parts[0].isdigit():
        parts = parts[1:]
    return ' '.join(part.capitalize() for part in parts)

def analyze_workflow_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Analyze a single workflow file and extract metadata."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Error reading {file_path}: {str(e)}")
        return None
    
    filename = os.path.basename(file_path)
    nodes = data.get('nodes', [])
    
    # Enhanced service mapping for better recognition
    service_mappings = {
        # AI/ML Services
        'openai': 'OpenAI',
        'lmchatopenai': 'OpenAI',
        'anthropic': 'Anthropic', 
        'agent': 'Agent',
        'chat': 'Chat',
        'memorybufferwindow': 'Memory Buffer',
        'chainllm': 'Chain LLM',
        'lmchatgooglegemini': 'Google Gemini',
        'lmchatollama': 'Ollama',
        'lmopenhuggingfaceinference': 'Hugging Face',
        'embeddingsgooglegemini': 'Google Embeddings',
        'toolhttprequest': 'HTTP Tool',
        'toolwikipedia': 'Wikipedia Tool',
        'executeworkflow': 'Execute Workflow',
        'documentdefaultdataloader': 'Document Loader',
        'outputparserstructured': 'Output Parser',
        
        # Messaging & Communication
        'telegram': 'Telegram',
        'telegramTrigger': 'Telegram',
        'discord': 'Discord',
        'slack': 'Slack', 
        'whatsapp': 'WhatsApp',
        'mattermost': 'Mattermost',
        
        # Email
        'gmail': 'Gmail',
        'gmailtool': 'Gmail',
        'emailreadimap': 'Email (IMAP)',
        'emailsendsmt': 'Email (SMTP)',
        
        # Cloud Storage
        'googledrive': 'Google Drive',
        'googledocs': 'Google Docs',
        'googlesheets': 'Google Sheets',
        'googlecalendar': 'Google Calendar', 
        'googlecalendartool': 'Google Calendar',
        'googletasks': 'Google Tasks',
        'dropbox': 'Dropbox',
        
        # Databases & Tools
        'postgres': 'PostgreSQL',
        'mysql': 'MySQL',
        'mongodb': 'MongoDB',
        'airtable': 'Airtable',
        'airtabletool': 'Airtable',
        'notion': 'Notion',
        
        # Project Management
        'github': 'GitHub',
        'gitlab': 'GitLab',
        'asana': 'Asana',
        
        # Forms & Triggers
        'typeform': 'Typeform',
        'form': 'Form Trigger',
        'webhook': 'Webhook',
        'httprequest': 'HTTP Request',
        'converttofile': 'Convert to File',
        'extractfromfile': 'Extract from File',
        'stickynote': 'Sticky Note',
        
        # Calendar & Scheduling
        'cal': 'Cal.com',
        'calendly': 'Calendly',
        'cron': 'Cron',
        'schedule': 'Schedule',
        
        # Other Services
        'hubspot': 'HubSpot',
        'stripe': 'Stripe',
        'paypal': 'PayPal',
    }
    
    # Analyze nodes for integrations and trigger type
    integrations = set()
    trigger_type = 'Manual'
    
    for node in nodes:
        node_type = node.get('type', '').lower()
        node_name = node.get('name', '').lower()
        
        # Determine trigger type
        if 'webhook' in node_type or 'webhook' in node_name:
            trigger_type = 'Webhook'
        elif 'cron' in node_type or 'schedule' in node_type:
            trigger_type = 'Scheduled'
        elif 'trigger' in node_type and trigger_type == 'Manual':
            if 'manual' not in node_type:
                trigger_type = 'Webhook'
        
        # Extract integrations with enhanced mapping
        service_name = None
        
        # Handle n8n-nodes-base nodes
        if node_type.startswith('n8n-nodes-base.'):
            raw_service = node_type.replace('n8n-nodes-base.', '').lower()
            raw_service = raw_service.replace('trigger', '')
            service_name = service_mappings.get(raw_service)
        
        # Handle @n8n/ namespaced nodes
        elif node_type.startswith('@n8n/'):
            raw_service = node_type.split('.')[-1].lower() if '.' in node_type else node_type.lower()
            raw_service = raw_service.replace('trigger', '')
            service_name = service_mappings.get(raw_service)
        
        # Check node names for service hints
        for service_key, service_value in service_mappings.items():
            if service_key in node_name and service_value:
                service_name = service_value
                break
        
        # Add to integrations if valid service found
        if service_name:
            integrations.add(service_name)
    
    node_count = len(nodes)
    
    # Determine if complex based on node variety and count
    if node_count > 10 and len(integrations) > 3:
        trigger_type = 'Complex'
    
    # Determine complexity
    if node_count <= 5:
        complexity = 'low'
    elif node_count <= 15:
        complexity = 'medium' 
    else:
        complexity = 'high'
    
    # Use JSON name if available and meaningful, otherwise use formatted filename
    json_name = data.get('name', '').strip()
    if json_name and json_name != filename.replace('.json', '') and not json_name.startswith('My workflow'):
        workflow_name = json_name
    else:
        workflow_name = format_workflow_name(filename)
    
    # Generate description
    desc = f"Workflow with {node_count} nodes"
    if integrations:
        main_services = list(integrations)[:3]
        if len(main_services) == 1:
            desc += f" using {main_services[0]}"
        elif len(main_services) == 2:
            desc += f" connecting {main_services[0]} and {main_services[1]}"
        else:
            desc += f" orchestrating {', '.join(main_services[:-1])}, and {main_services[-1]}"
        
        if trigger_type == 'Complex':
            desc = f"Complex multi-step automation that {desc.replace('Workflow with', '').replace(' nodes', ' nodes and')}"
        elif trigger_type == 'Webhook':
            desc = f"Webhook-triggered automation that {desc.replace('Workflow with', '').replace(' nodes', ' nodes and')}"
        elif trigger_type == 'Scheduled':
            desc = f"Scheduled automation that {desc.replace('Workflow with', '').replace(' nodes', ' nodes and')}"
        
        if 'create' in workflow_name.lower():
            desc += " to create new records"
        elif 'update' in workflow_name.lower():
            desc += " to update existing data"
        elif 'sync' in workflow_name.lower():
            desc += " to synchronize data"
        elif 'process' in workflow_name.lower():
            desc += " for data processing"
        elif 'automation' in workflow_name.lower():
            desc += " for automation tasks"
        else:
            desc += " for data processing"
    
    desc += f". Uses {node_count} nodes"
    if len(integrations) > 3:
        desc += f" and integrates with {len(integrations)} services"
    desc += "."
    
    return {
        'filename': filename,
        'name': workflow_name,
        'workflow_id': data.get('id', ''),
        'active': data.get('active', False),
        'description': desc,
        'trigger_type': trigger_type,
        'complexity': complexity,
        'node_count': node_count,
        'integrations': sorted(list(integrations)),
        'tags': data.get('tags', []),
        'created_at': data.get('createdAt', ''),
        'updated_at': data.get('updatedAt', ''),
        'file_hash': get_file_hash(file_path),
        'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        'content': extract_workflow_content(data)
    }

def extract_workflow_content(data: Dict[str, Any]) -> str:
    """Extract all searchable content from workflow JSON including nodes, parameters, and sticky notes."""
    content_parts = []
    
    # Extract basic workflow info
    if 'name' in data:
        content_parts.append(str(data['name']))
    
    if 'description' in data:
        content_parts.append(str(data['description']))
    
    # Extract content from nodes
    if 'nodes' in data:
        for node in data['nodes']:
            # Node type and name
            if 'type' in node:
                content_parts.append(str(node['type']))
            if 'name' in node:
                content_parts.append(str(node['name']))
            
            # Node parameters and configuration
            if 'parameters' in node:
                params = node['parameters']
                if isinstance(params, dict):
                    for key, value in params.items():
                        if isinstance(value, str):
                            content_parts.append(f"{key}: {value}")
                        elif isinstance(value, dict):
                            content_parts.append(str(value))
                        else:
                            content_parts.append(f"{key}: {str(value)}")
            
            # Sticky note content
            if node.get('type') == 'n8n-nodes-base.stickyNote':
                if 'parameters' in node and 'content' in node['parameters']:
                    content_parts.append(str(node['parameters']['content']))
            
            # Code node content
            if node.get('type') == 'n8n-nodes-base.code':
                if 'parameters' in node and 'jsCode' in node['parameters']:
                    content_parts.append(str(node['parameters']['jsCode']))
    
    # Extract tags
    if 'tags' in data and isinstance(data['tags'], list):
        for tag in data['tags']:
            content_parts.append(str(tag))
    
    return ' '.join(content_parts)

def build_vercel_data_dict():
    """Build workflow data for Vercel deployment and return as dictionary."""
    workflows_dir = "workflows"
    if not os.path.exists(workflows_dir):
        print(f"Warning: Workflows directory '{workflows_dir}' not found.")
        return {'stats': {}, 'workflows': []}
    
    workflows_path = Path(workflows_dir)
    json_files = list(workflows_path.rglob("*.json"))
    
    if not json_files:
        print(f"Warning: No JSON files found in '{workflows_dir}' directory.")
        return {'stats': {}, 'workflows': []}
    
    print(f"Processing {len(json_files)} workflow files...")
    
    workflows_data = []
    errors = 0
    
    for i, file_path in enumerate(json_files):
        workflow_data = analyze_workflow_file(str(file_path))
        if workflow_data:
            workflows_data.append(workflow_data)
        else:
            errors += 1
        
        # Progress indicator
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(json_files)} workflows...")
    
    # Calculate statistics
    total = len(workflows_data)
    active = sum(1 for w in workflows_data if w['active'])
    total_nodes = sum(w['node_count'] for w in workflows_data)
    
    triggers = {}
    complexity = {}
    all_integrations = set()
    
    for workflow in workflows_data:
        # Trigger stats
        trigger = workflow['trigger_type']
        triggers[trigger] = triggers.get(trigger, 0) + 1
        
        # Complexity stats
        comp = workflow['complexity']
        complexity[comp] = complexity.get(comp, 0) + 1
        
        # Integrations
        all_integrations.update(workflow['integrations'])
    
    stats = {
        'total': total,
        'active': active,
        'inactive': total - active,
        'triggers': triggers,
        'complexity': complexity,
        'total_nodes': total_nodes,
        'unique_integrations': len(all_integrations),
        'last_indexed': '2025-08-21'
    }
    
    # Build final data structure
    vercel_data = {
        'stats': stats,
        'workflows': workflows_data,
        'generated_at': '2025-08-21T00:00:00Z',
        'version': '1.0'
    }
    
    return vercel_data

def build_vercel_data():
    """Build workflow data for Vercel deployment."""
    vercel_data = build_vercel_data_dict()
    
    # Write to JSON file
    output_file = 'vercel_workflows.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(vercel_data, f, separators=(',', ':'))  # Compact format
    
    file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
    stats = vercel_data['stats']
    
    print(f"✅ Built Vercel data: {output_file}")
    print(f"📊 Processed: {stats['total']} workflows")
    print(f"📁 File size: {file_size:.1f} MB")
    print(f"🔢 Statistics: {stats['total']} total, {stats['active']} active, {stats['total_nodes']:,} nodes")
    print(f"🔌 Unique integrations: {stats['unique_integrations']}")

if __name__ == "__main__":
    build_vercel_data()