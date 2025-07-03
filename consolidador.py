#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolidador de Dados Multi-Site
================================

Normaliza e consolida dados de todos os sites em formato único.
"""

import os
import json
import glob
from datetime import datetime
from typing import Dict, List, Any, Optional


class DataConsolidator:
    """Consolidador de dados do sistema multi-site"""
    
    def __init__(self):
        self.site_configs = {
            'tripadvisor': {
                'nome': 'TripAdvisor',
                'rating_scale': '1-5',
                'extraction_method': 'GraphQL API',
                'description': 'Maior plataforma de reviews de turismo do mundo'
            },
            'booking': {
                'nome': 'Booking.com',
                'rating_scale': '1-10',
                'extraction_method': 'HTML Parsing + Anti-block',
                'description': 'Líder mundial em reservas de hospedagem'
            },
            'google': {
                'nome': 'Google Places',
                'rating_scale': '1-5',
                'extraction_method': 'Official Places API',
                'description': 'API oficial do Google com dados em tempo real'
            },
            'decolar': {
                'nome': 'Decolar',
                'rating_scale': '1-10',
                'extraction_method': 'HTML Parsing + Fallback',
                'description': 'Maior OTA da América Latina'
            }
        }
    
    def _normalize_hotel_data(self, hotel_data: Dict[str, Any], site: str) -> Dict[str, Any]:
        """Normaliza dados de um hotel para estrutura padrão"""
        normalized = {
            'hotel_id': '',
            'hotel_name': '',
            'rating': 0.0,
            'review_count': 0,
            'max_rating': 5.0,
            'url': '',
            'source': '',
            'data_source': '',
            'extraction_timestamp': '',
            'site': site,
            'additional_info': {}
        }
        
        if site == 'tripadvisor':
            normalized.update({
                'hotel_id': hotel_data.get('hotel_id', ''),
                'hotel_name': hotel_data.get('hotel_name', ''),
                'rating': float(hotel_data.get('rating', 0)),
                'review_count': int(hotel_data.get('review_count', 0)),
                'max_rating': 5.0,
                'url': hotel_data.get('hotel_url', ''),
                'source': hotel_data.get('source', ''),
                'data_source': hotel_data.get('data_source', ''),
                'extraction_timestamp': hotel_data.get('extraction_timestamp', ''),
                'additional_info': {
                    'reviews': hotel_data.get('reviews', [])
                }
            })
            
        elif site == 'booking':
            normalized.update({
                'hotel_id': self._generate_hotel_id(hotel_data.get('hotel_name', '')),
                'hotel_name': hotel_data.get('hotel_name', ''),
                'rating': float(hotel_data.get('rating', 0)),
                'review_count': int(hotel_data.get('reviews', 0)),
                'max_rating': float(hotel_data.get('max_rating', 10.0)),
                'url': hotel_data.get('url', ''),
                'source': hotel_data.get('source', ''),
                'data_source': 'html_parsing',
                'extraction_timestamp': hotel_data.get('timestamp', ''),
                'additional_info': {}
            })
            
        elif site == 'google':
            normalized.update({
                'hotel_id': hotel_data.get('hotel_id', ''),
                'hotel_name': hotel_data.get('hotel_name', ''),
                'rating': float(hotel_data.get('rating', 0)),
                'review_count': int(hotel_data.get('review_count', 0)),
                'max_rating': float(hotel_data.get('max_rating', 5.0)),
                'url': hotel_data.get('google_url', ''),
                'source': hotel_data.get('source', ''),
                'data_source': hotel_data.get('data_source', ''),
                'extraction_timestamp': hotel_data.get('extraction_timestamp', ''),
                'additional_info': {
                    'hotel_search_term': hotel_data.get('hotel_search_term', '')
                }
            })
            
        elif site == 'decolar':
            normalized.update({
                'hotel_id': hotel_data.get('hotel_id', ''),
                'hotel_name': hotel_data.get('hotel_name', ''),
                'rating': float(hotel_data.get('rating', 0)),
                'review_count': int(hotel_data.get('review_count', 0)),
                'max_rating': 10.0,
                'url': hotel_data.get('hotel_url', ''),
                'source': hotel_data.get('source', ''),
                'data_source': hotel_data.get('data_source', ''),
                'extraction_timestamp': hotel_data.get('extraction_timestamp', ''),
                'additional_info': {
                    'reviews': hotel_data.get('reviews', [])
                }
            })
        
        return normalized
    
    def _generate_hotel_id(self, hotel_name: str) -> str:
        """Gera ID único baseado no nome do hotel"""
        return hotel_name.lower().replace(' ', '_').replace('hotel_', '').replace('ç', 'c').replace('ã', 'a')
    
    def load_site_data(self, site: str, results_dir: str = 'resultados') -> Optional[Dict[str, Any]]:
        """Carrega dados mais recentes de um site"""
        pattern = f"{results_dir}/{site}_dados_*.json"
        files = glob.glob(pattern)
        
        if not files:
            print(f"Nenhum arquivo encontrado para {site}")
            return None
        
        latest_file = max(files, key=os.path.getctime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"{site.capitalize()}: {latest_file}")
            return data
            
        except Exception as e:
            print(f"Erro ao carregar {latest_file}: {e}")
            return None
    
    def normalize_site_data(self, site_data: Dict[str, Any], site: str) -> Dict[str, Any]:
        """Normaliza todos os dados de um site"""
        normalized_hotels = []
        
        for hotel in site_data.get('hoteis', []):
            normalized_hotel = self._normalize_hotel_data(hotel, site)
            normalized_hotels.append(normalized_hotel)
        
        metadata = site_data.get('metadata', {})
        
        return {
            'site_info': self.site_configs.get(site, {}),
            'metadata': {
                'total_hoteis': len(normalized_hotels),
                'timestamp_extracao': metadata.get('timestamp_extracao', ''),
                'versao_scraper': metadata.get('versao_scraper', ''),
                'extraction_stats': {
                    'sucesso': len(normalized_hotels),
                    'total_avaliacoes': sum(h['review_count'] for h in normalized_hotels),
                    'rating_medio': round(sum(h['rating'] for h in normalized_hotels) / len(normalized_hotels), 2) if normalized_hotels else 0
                }
            },
            'hoteis': normalized_hotels
        }
    
    def generate_consolidated_json(self, results_dir: str = 'resultados') -> Optional[str]:
        """Gera JSON consolidado com dados de todos os sites"""
        print("GERANDO JSON CONSOLIDADO")
        print("=" * 50)
        
        consolidated_data = {
            'metadata': {
                'timestamp_consolidacao': datetime.now().isoformat(),
                'versao_sistema': '2.0.0-multi-site',
                'total_sites': 0,
                'total_hoteis': 0,
                'total_avaliacoes': 0,
                'rating_medio_geral': 0.0
            },
            'sites': {}
        }
        
        sites = ['tripadvisor', 'booking', 'google', 'decolar']
        all_ratings = []
        total_reviews = 0
        total_hotels = 0
        
        for site in sites:
            print(f"\nProcessando {site.capitalize()}...")
            
            site_data = self.load_site_data(site, results_dir)
            if site_data:
                normalized_site = self.normalize_site_data(site_data, site)
                consolidated_data['sites'][site] = normalized_site
                
                site_hotels = normalized_site['hoteis']
                total_hotels += len(site_hotels)
                total_reviews += sum(h['review_count'] for h in site_hotels)
                all_ratings.extend(h['rating'] for h in site_hotels)
                
                print(f"   {len(site_hotels)} hotéis normalizados")
            else:
                print(f"   Dados não encontrados")
        
        consolidated_data['metadata'].update({
            'total_sites': len(consolidated_data['sites']),
            'total_hoteis': total_hotels,
            'total_avaliacoes': total_reviews,
            'rating_medio_geral': round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else 0
        })
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{results_dir}/scraper_dados_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(consolidated_data, f, ensure_ascii=False, indent=2)
            
            print(f"\nArquivo consolidado salvo: {filename}")
            
            print(f"\nESTATÍSTICAS CONSOLIDADAS:")
            print(f"   Sites processados: {consolidated_data['metadata']['total_sites']}")
            print(f"   Total de hotéis: {consolidated_data['metadata']['total_hoteis']}")
            print(f"   Rating médio geral: {consolidated_data['metadata']['rating_medio_geral']}")
            print(f"   Total de avaliações: {consolidated_data['metadata']['total_avaliacoes']:,}")
            
            return filename
            
        except Exception as e:
            print(f"Erro ao salvar consolidado: {e}")
            return None
    
    def update_individual_jsons(self, results_dir: str = 'resultados') -> Dict[str, str]:
        """Atualiza JSONs individuais com estrutura normalizada"""
        print("\nATUALIZANDO JSONs INDIVIDUAIS")
        print("=" * 50)
        
        updated_files = {}
        sites = ['tripadvisor', 'booking', 'google', 'decolar']
        
        for site in sites:
            print(f"\nNormalizando {site.capitalize()}...")
            
            site_data = self.load_site_data(site, results_dir)
            if site_data:
                normalized_site = self.normalize_site_data(site_data, site)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{results_dir}/{site}_normalizado_{timestamp}.json"
                
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(normalized_site, f, ensure_ascii=False, indent=2)
                    
                    print(f"   Salvo: {filename}")
                    updated_files[site] = filename
                    
                except Exception as e:
                    print(f"   Erro ao salvar: {e}")
            else:
                print(f"   Dados não encontrados")
        
        return updated_files


def main():
    """Função principal para testar o consolidador"""
    consolidator = DataConsolidator()
    
    updated_files = consolidator.update_individual_jsons()
    consolidated_file = consolidator.generate_consolidated_json()
    
    if consolidated_file:
        print(f"\nCONSOLIDAÇÃO CONCLUÍDA!")
        print(f"Arquivo consolidado: {consolidated_file}")
        print(f"Arquivos individuais: {len(updated_files)}")


if __name__ == "__main__":
    main() 