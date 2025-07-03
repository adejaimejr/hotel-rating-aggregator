#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hotel Rating Aggregator
=======================

Sistema orquestrador para scraping multi-site de avaliações de hotéis.
Suporta TripAdvisor, Booking.com, Google Places e Decolar.
"""

import os
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

from sites.tripadvisor.scraper import TripAdvisorScraper
from sites.booking.scraper import BookingScraper
from sites.google.scraper import GoogleTravelScraper
from sites.decolar.scraper import DecolarScraper
from consolidador import DataConsolidator


class HotelScrapingOrchestrator:
    """Orquestrador principal do sistema de scraping multi-sites"""
    
    def __init__(self, config_file: str = "config.env"):
        self.config_file = config_file
        self.config = self._load_config()
        self.scrapers = self._initialize_scrapers()
        
    def _load_config(self) -> Dict[str, str]:
        """Carrega configurações do arquivo .env"""
        config = {}
        
        if not os.path.exists(self.config_file):
            print(f"Arquivo de configuração não encontrado: {self.config_file}")
            return config
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
                        
            print(f"Configurações carregadas: {len(config)} variáveis")
            return config
            
        except Exception as e:
            print(f"Erro ao carregar configurações: {e}")
            return {}
    
    def _initialize_scrapers(self) -> Dict[str, Any]:
        """Inicializa scrapers para todos os sites"""
        return {
            'tripadvisor': TripAdvisorScraper(),
            'booking': BookingScraper(),
            'google': GoogleTravelScraper(),
            'decolar': DecolarScraper()
        }
    
    def _get_hotels_config_for_site(self, site: str) -> Dict[str, str]:
        """Extrai configuração de hotéis para um site específico"""
        hotels_config = {}
        site_upper = site.upper()
        
        excluded_keys = {
            'GOOGLE_API_KEY', 'GOOGLE_SERVICE_ACCOUNT_JSON', 
            'GOOGLE_API_TIMEOUT', 'GOOGLE_API_DELAY'
        }
        
        for key, value in self.config.items():
            if (key.startswith(f"{site_upper}_") and 
                not key.endswith("_ID") and 
                not key.endswith("_NAME") and
                key not in excluded_keys):
                
                hotel_key = key.replace(f"{site_upper}_", "")
                
                # Verifica se existe uma variável _NAME específica para este hotel
                name_key = f"{site_upper}_{hotel_key}_NAME"
                if name_key in self.config:
                    hotel_name = self.config[name_key]
                else:
                    # Fallback para o método antigo de gerar nome
                    hotel_name = self._format_hotel_name(hotel_key)
                
                hotels_config[hotel_name] = value
        
        return hotels_config
    
    def _format_hotel_name(self, hotel_key: str) -> str:
        """Converte chave de configuração em nome de exibição do hotel"""
        words = hotel_key.lower().replace('_', ' ').split()
        formatted_words = []
        
        for word in words:
            if word in ['de', 'da', 'do', 'das', 'dos', 'e']:
                formatted_words.append(word)
            else:
                formatted_words.append(word.capitalize())
        
        formatted_name = ' '.join(formatted_words)
        if not formatted_name.lower().startswith('hotel') and not any(formatted_name.lower().startswith(prefix) for prefix in ['maragogi', 'pousada', 'resort']):
            formatted_name = f"Hotel {formatted_name}"
        
        return formatted_name
    
    def _save_results_to_json(self, site: str, results: List[Dict[str, Any]]) -> str:
        """Salva resultados em arquivo JSON específico do site"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"resultados/{site}_dados_{timestamp}.json"
        
        os.makedirs("resultados", exist_ok=True)
        
        output_data = {
            "metadata": {
                "site": site,
                "total_hoteis": len(results),
                "timestamp_extracao": datetime.now().isoformat(),
                "versao_scraper": "2.0.0-multi-site"
            },
            "hoteis": results
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            print(f"Dados salvos: {filename}")
            return filename
            
        except Exception as e:
            print(f"Erro ao salvar arquivo: {e}")
            return ""
    
    def scrape_site(self, site: str) -> Optional[str]:
        """Executa scraping para um site específico"""
        if site not in self.scrapers:
            print(f"Site não suportado: {site}")
            return None
        
        print(f"\nIniciando scraping do {site.upper()}")
        print("=" * 50)
        
        hotels_config = self._get_hotels_config_for_site(site)
        
        if not hotels_config:
            print(f"Nenhum hotel configurado para {site}")
            return None
        
        print(f"Hotéis configurados para {site}: {len(hotels_config)}")
        
        scraper = self.scrapers[site]
        results = scraper.scrape_multiple_hotels(hotels_config)
        
        if results:
            json_file = self._save_results_to_json(site, results)
            print(f"{site.upper()} concluído: {len(results)} hotéis processados")
            return json_file
        else:
            print(f"Nenhum resultado obtido para {site}")
            return None
    
    def scrape_all_sites(self) -> Dict[str, str]:
        """Executa scraping para todos os sites configurados"""
        results = {}
        available_sites = ['tripadvisor', 'booking', 'google', 'decolar']
        
        print("INICIANDO SCRAPING MULTI-SITE")
        print("=" * 60)
        print(f"Sites disponíveis: {', '.join(available_sites)}")
        print(f"Total de hotéis por site: {len(self._get_hotels_config_for_site('tripadvisor'))}")
        
        for site in available_sites:
            try:
                json_file = self.scrape_site(site)
                if json_file:
                    results[site] = json_file
                    
                if site != available_sites[-1]:
                    print(f"Pausa entre sites...")
                    import time
                    time.sleep(2)
                    
            except Exception as e:
                print(f"Erro ao processar {site}: {e}")
                continue
        
        # Consolida dados e limpa arquivos individuais
        if results:
            consolidated_file = self.consolidate_data()
            if consolidated_file:
                self._cleanup_individual_files(results)
        
        return results
    
    def consolidate_data(self) -> Optional[str]:
        """Gera JSON consolidado com dados normalizados de todos os sites"""
        print(f"\nINICIANDO CONSOLIDAÇÃO DE DADOS")
        print("=" * 60)
        
        try:
            consolidator = DataConsolidator()
            consolidated_file = consolidator.generate_consolidated_json()
            
            if consolidated_file:
                print(f"Consolidação concluída: {consolidated_file}")
                return consolidated_file
            else:
                print("Erro na consolidação")
                return None
                
        except Exception as e:
            print(f"Erro durante consolidação: {e}")
            return None
    
    def _cleanup_individual_files(self, results: Dict[str, str]) -> None:
        """Remove arquivos individuais após consolidação"""
        import os
        
        print("Limpando arquivos individuais...")
        for site, file_path in results.items():
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"   Removido: {file_path}")
            except Exception as e:
                print(f"   Erro ao remover {file_path}: {e}")
    
    def show_status(self):
        """Mostra status das configurações e scrapers"""
        print("STATUS DO SISTEMA")
        print("=" * 40)
        
        print(f"Arquivo de config: {self.config_file}")
        print(f"Configurações carregadas: {len(self.config)}")
        
        print(f"\nScrapers disponíveis:")
        for site, scraper in self.scrapers.items():
            implemented = getattr(scraper, 'implemented', True)
            status = "Funcional" if implemented else "Em desenvolvimento"
            print(f"   {site.capitalize()}: {status}")
        
        print(f"\nHotéis configurados por site:")
        for site in self.scrapers.keys():
            hotels = self._get_hotels_config_for_site(site)
            print(f"   {site.capitalize()}: {len(hotels)} hotéis")


def main():
    """Função principal com argumentos de linha de comando"""
    parser = argparse.ArgumentParser(
        description="Sistema Multi-Site de Scraping de Hotéis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py                    # Executa todos os sites + consolidação
  python main.py --site tripadvisor # Executa apenas TripAdvisor
  python main.py --status           # Mostra status do sistema
  python main.py --sites booking decolar # Executa sites específicos
  python main.py --consolidar       # Gera apenas JSON consolidado
        """
    )
    
    parser.add_argument(
        '--site', 
        choices=['tripadvisor', 'booking', 'google', 'decolar'],
        help='Executa scraping para um site específico'
    )
    
    parser.add_argument(
        '--sites',
        nargs='+',
        choices=['tripadvisor', 'booking', 'google', 'decolar'],
        help='Executa scraping para múltiplos sites específicos'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Mostra status das configurações e scrapers'
    )
    
    parser.add_argument(
        '--config',
        default='config.env',
        help='Caminho para arquivo de configuração (padrão: config.env)'
    )
    
    parser.add_argument(
        '--consolidar',
        action='store_true',
        help='Gera apenas JSON consolidado a partir dos dados existentes'
    )
    
    args = parser.parse_args()
    
    orchestrator = HotelScrapingOrchestrator(args.config)
    
    if args.status:
        orchestrator.show_status()
        
    elif args.consolidar:
        consolidated_file = orchestrator.consolidate_data()
        if consolidated_file:
            print(f"\nArquivo consolidado gerado: {consolidated_file}")
        
    elif args.site:
        json_file = orchestrator.scrape_site(args.site)
        if json_file:
            print(f"\nArquivo gerado: {json_file}")
            
    elif args.sites:
        results = {}
        for site in args.sites:
            json_file = orchestrator.scrape_site(site)
            if json_file:
                results[site] = json_file
        
        print(f"\nArquivos gerados: {len(results)}")
        for site, file_path in results.items():
            print(f"   {site.capitalize()}: {file_path}")
            
    else:
        results = orchestrator.scrape_all_sites()
        
        print(f"\nSCRAPING CONCLUÍDO")
        print("=" * 30)
        print(f"Sites processados: {len(results)}")
        
        for site, file_path in results.items():
            print(f"{site.capitalize()}: {file_path}")


if __name__ == "__main__":
    main() 