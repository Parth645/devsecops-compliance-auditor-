"""
Data Flow Extractor - Intelligent Route & Model Analysis
Extracts application routes and their corresponding database models
for targeted business logic compliance analysis
"""

import logging
import re
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class DataFlowExtractor:
    """
    Extracts application data flows by identifying:
    1. API Routes/Endpoints
    2. Database Models/Schemas
    3. Request-to-Database mappings
    
    Used for targeted Groq analysis of compliance logic
    """
    
    def __init__(self):
        """Initialize data flow extractor"""
        self.routes = []
        self.models = []
        self.flows = []
        logger.info("✓ Data Flow Extractor initialized")
    
    def extract_from_repository(self, repo_path: str) -> Dict[str, Any]:
        """
        Extract data flows from entire repository
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Dictionary containing routes, models, and data flows
        """
        result = {
            'routes': [],
            'models': [],
            'data_flows': [],
            'analysis_targets': []
        }
        
        # Find and parse route files
        route_files = self._find_route_files(repo_path)
        result['routes'] = self._parse_routes(route_files)
        
        # Find and parse model files
        model_files = self._find_model_files(repo_path)
        result['models'] = self._parse_models(model_files)
        
        # Match routes to models
        result['data_flows'] = self._match_flows(result['routes'], result['models'])
        
        # Generate analysis targets (high-priority flows for LLM analysis)
        result['analysis_targets'] = self._generate_analysis_targets(result['data_flows'])
        
        return result
    
    def _find_route_files(self, repo_path: str) -> List[str]:
        """Find all route/controller files"""
        route_patterns = [
            '**/*routes.js', '**/*routes.ts',
            '**/*routes.py',
            '**/*controller.js', '**/*controller.ts',
            '**/*handlers.js', '**/*handlers.ts',
            '**/api/**/*.js', '**/api/**/*.ts', '**/api/**/*.py',
            '**/routes/**/*.js', '**/routes/**/*.ts',
            '**/handlers/**/*.js', '**/handlers/**/*.ts',
            'src/routes/*', 'src/controllers/*', 'src/handlers/*',
            'app/routes/*', 'app/controllers/*'
        ]
        
        files = []
        path = Path(repo_path)
        for pattern in route_patterns:
            files.extend([str(f) for f in path.glob(pattern) if f.is_file()])
        
        return list(set(files))
    
    def _find_model_files(self, repo_path: str) -> List[str]:
        """Find all model/schema files"""
        model_patterns = [
            '**/*model.js', '**/*model.ts',
            '**/*model.py',
            '**/*schema.js', '**/*schema.ts',
            '**/*entity.ts', '**/*entity.py',
            '**/models/**/*.js', '**/models/**/*.ts', '**/models/**/*.py',
            '**/schemas/**/*.js', '**/schemas/**/*.ts',
            'src/models/*', 'src/schemas/*', 'src/entities/*',
            'app/models/*', 'app/schemas/*'
        ]
        
        files = []
        path = Path(repo_path)
        for pattern in model_patterns:
            files.extend([str(f) for f in path.glob(pattern) if f.is_file()])
        
        return list(set(files))
    
    def _parse_routes(self, route_files: List[str]) -> List[Dict[str, Any]]:
        """Parse route definitions from files"""
        routes = []
        
        for file_path in route_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract Express routes (JavaScript/TypeScript)
                routes.extend(self._extract_express_routes(file_path, content))
                
                # Extract Flask routes (Python)
                routes.extend(self._extract_flask_routes(file_path, content))
                
                # Extract FastAPI routes (Python)
                routes.extend(self._extract_fastapi_routes(file_path, content))
                
            except Exception as e:
                logger.debug(f"Error parsing routes from {file_path}: {e}")
        
        return routes
    
    def _extract_express_routes(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract Express.js routes"""
        routes = []
        
        # Match patterns like: app.post('/api/users', handler) or router.post('/users', ...)
        patterns = [
            r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
            r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*`([^`]+)`'
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                method = match.group(1).upper()
                path = match.group(2)
                
                # Extract handler function name if available
                handler_match = re.search(
                    r'(?:app|router)\.' + re.escape(method.lower()) + r'\s*\([^,]+,\s*(\w+)',
                    content[match.start():match.start()+200]
                )
                handler = handler_match.group(1) if handler_match else 'unknown'
                
                routes.append({
                    'file': file_path,
                    'type': 'express',
                    'method': method,
                    'path': path,
                    'handler': handler,
                    'sensitive': self._is_sensitive_endpoint(path)
                })
        
        return routes
    
    def _extract_flask_routes(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract Flask routes"""
        routes = []
        
        # Match @app.route('/path', methods=['GET', 'POST'])
        for match in re.finditer(r'@(?:app|bp)\.route\s*\(\s*["\']([^"\']+)["\']', content):
            path = match.group(1)
            
            # Find associated function
            func_match = re.search(
                r'def\s+(\w+)\s*\(',
                content[match.end():match.end()+200]
            )
            handler = func_match.group(1) if func_match else 'unknown'
            
            routes.append({
                'file': file_path,
                'type': 'flask',
                'method': 'GET',  # Flask defaults to GET
                'path': path,
                'handler': handler,
                'sensitive': self._is_sensitive_endpoint(path)
            })
        
        return routes
    
    def _extract_fastapi_routes(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract FastAPI routes"""
        routes = []
        
        # Match @app.post('/path'), @app.get('/path')
        for match in re.finditer(r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', content):
            method = match.group(1).upper()
            path = match.group(2)
            
            # Find function
            func_match = re.search(
                r'async def\s+(\w+)\s*\(',
                content[match.end():match.end()+200]
            )
            handler = func_match.group(1) if func_match else 'unknown'
            
            routes.append({
                'file': file_path,
                'type': 'fastapi',
                'method': method,
                'path': path,
                'handler': handler,
                'sensitive': self._is_sensitive_endpoint(path)
            })
        
        return routes
    
    def _parse_models(self, model_files: List[str]) -> List[Dict[str, Any]]:
        """Parse database model definitions"""
        models = []
        
        for file_path in model_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract Mongoose models (JavaScript)
                models.extend(self._extract_mongoose_models(file_path, content))
                
                # Extract SQLAlchemy models (Python)
                models.extend(self._extract_sqlalchemy_models(file_path, content))
                
                # Extract Sequelize models (JavaScript)
                models.extend(self._extract_sequelize_models(file_path, content))
                
            except Exception as e:
                logger.debug(f"Error parsing models from {file_path}: {e}")
        
        return models
    
    def _extract_mongoose_models(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract Mongoose schema definitions"""
        models = []
        
        # Match: const userSchema = new Schema({ ... })
        for match in re.finditer(
            r'(?:const|var)\s+(\w+Schema)\s*=\s*new\s+Schema\s*\(\s*\{([^}]*)\}',
            content, re.DOTALL
        ):
            schema_name = match.group(1)
            fields_str = match.group(2)
            
            # Extract field names and types
            fields = {}
            for field_match in re.finditer(r'(\w+)\s*:\s*\{?\s*type\s*:\s*(\w+)', fields_str):
                field_name = field_match.group(1)
                field_type = field_match.group(2)
                
                # Check if field is sensitive
                is_pii = field_name.lower() in ['email', 'phone', 'ssn', 'aadhaar', 'password', 'creditcard']
                fields[field_name] = {
                    'type': field_type,
                    'is_pii': is_pii
                }
            
            models.append({
                'file': file_path,
                'type': 'mongoose',
                'name': schema_name.replace('Schema', ''),
                'fields': fields,
                'pii_fields': [f for f, props in fields.items() if props['is_pii']]
            })
        
        return models
    
    def _extract_sqlalchemy_models(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract SQLAlchemy model definitions"""
        models = []
        
        # Match: class User(Base):
        for match in re.finditer(r'class\s+(\w+)\s*\(\s*Base\s*\):', content):
            model_name = match.group(1)
            
            # Extract columns from that class
            model_start = match.end()
            model_end = content.find('\nclass ', model_start)
            if model_end == -1:
                model_end = len(content)
            
            model_content = content[model_start:model_end]
            
            # Find Column definitions
            fields = {}
            pii_fields = []
            
            for col_match in re.finditer(r'(\w+)\s*=\s*Column\s*\(([^)]+)\)', model_content):
                field_name = col_match.group(1)
                field_def = col_match.group(2)
                
                # Extract type
                type_match = re.search(r'(String|Integer|DateTime|Boolean|Text|Float)', field_def)
                field_type = type_match.group(1) if type_match else 'Unknown'
                
                # Check if sensitive
                is_pii = field_name.lower() in ['email', 'phone', 'ssn', 'aadhaar', 'password', 'credit_card']
                fields[field_name] = {
                    'type': field_type,
                    'is_pii': is_pii
                }
                
                if is_pii:
                    pii_fields.append(field_name)
            
            models.append({
                'file': file_path,
                'type': 'sqlalchemy',
                'name': model_name,
                'fields': fields,
                'pii_fields': pii_fields
            })
        
        return models
    
    def _extract_sequelize_models(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract Sequelize model definitions"""
        models = []
        
        # Match: module.exports = (sequelize, DataTypes) => { ... }
        if 'sequelize' in content.lower() and 'define' in content.lower():
            for match in re.finditer(r'sequelize\.define\s*\(\s*["\'](\w+)["\']', content):
                model_name = match.group(1)
                
                # For Sequelize, we'd need more complex parsing
                # Simplified version for now
                models.append({
                    'file': file_path,
                    'type': 'sequelize',
                    'name': model_name,
                    'fields': {},
                    'pii_fields': []
                })
        
        return models
    
    def _match_flows(self, routes: List[Dict], models: List[Dict]) -> List[Dict[str, Any]]:
        """Match routes to their corresponding models"""
        flows = []
        
        for route in routes:
            if not route['sensitive']:
                continue  # Skip non-sensitive routes
            
            # Try to match route to model by path/handler name
            path = route['path'].lower()
            handler = route['handler'].lower()
            
            for model in models:
                model_name = model['name'].lower()
                
                # Check if route path contains model name
                if model_name in path or model_name in handler:
                    flows.append({
                        'route': route,
                        'model': model,
                        'route_path': route['path'],
                        'model_name': model['name'],
                        'pii_involved': len(model['pii_fields']) > 0,
                        'pii_fields': model['pii_fields'],
                        'priority': 'high' if len(model['pii_fields']) > 0 else 'medium'
                    })
        
        return flows
    
    def _generate_analysis_targets(self, flows: List[Dict]) -> List[Dict[str, Any]]:
        """Generate high-priority targets for LLM analysis"""
        targets = []
        
        # Sort by priority
        high_priority = [f for f in flows if f['priority'] == 'high']
        medium_priority = [f for f in flows if f['priority'] == 'medium']
        
        # Add high-priority flows first (limit to 10 total)
        for flow in high_priority[:10]:
            targets.append({
                'type': 'data_flow',
                'route': flow['route_path'],
                'model': flow['model_name'],
                'pii_fields': flow['pii_fields'],
                'analysis_focus': [
                    f"Does {flow['route_path']} verify user consent before processing {', '.join(flow['pii_fields'])}?",
                    f"Is data minimization enforced? Are all fields in {flow['model_name']} necessary?",
                    f"Are {flow['pii_fields']} encrypted and logged?"
                ]
            })
        
        # Add medium-priority flows to fill up to 10 total targets
        remaining_slots = 10 - len(targets)
        for flow in medium_priority[:remaining_slots]:
            targets.append({
                'type': 'data_flow',
                'route': flow['route_path'],
                'model': flow['model_name'],
                'pii_fields': flow['pii_fields'],
                'analysis_focus': [
                    f"Does {flow['route_path']} verify user consent before processing {', '.join(flow['pii_fields'])}?",
                    f"Is data minimization enforced? Are all fields in {flow['model_name']} necessary?",
                    f"Are {flow['pii_fields']} encrypted and logged?"
                ]
            })
        
        return targets
    
    @staticmethod
    def _is_sensitive_endpoint(path: str) -> bool:
        """Determine if endpoint is sensitive (deals with personal data)"""
        sensitive_keywords = [
            'user', 'profile', 'account', 'personal', 'auth', 'login',
            'register', 'payment', 'transaction', 'data', 'customer',
            'aadhaar', 'pan', 'email', 'phone', 'ssn', 'health', 'financial'
        ]
        
        path_lower = path.lower()
        return any(keyword in path_lower for keyword in sensitive_keywords)
