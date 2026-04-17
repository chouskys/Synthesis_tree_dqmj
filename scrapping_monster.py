from bs4 import BeautifulSoup
import requests
import pandas as pd
import os 
import regex as re
from urllib.parse import unquote


class MonstersBanks:
    def __init__(self):
        self.api_url = "https://dqmj.fandom.com/api.php"
        self.base_url = "https://dqmj.fandom.com"
        

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
        })

        self.links = self.get_all_monsters_link()
        self.syn_dataframe = self.get_synthese_monster()
        

    def _get_page_html_via_api(self, page_name: str, index=None) -> str:
        params = {
            "action": "parse",
            "page": page_name,
            "prop": "text",
            "format": "json",
        }

        r = self.session.get(self.api_url, params=params, timeout=30)
        print("api status:", r.status_code, index, page_name)
        r.raise_for_status()

        data = r.json()
        return data["parse"]["text"]["*"]

    def get_all_monsters_link(self):
        html = self._get_page_html_via_api("Monster_list")
        soup = BeautifulSoup(html, "html.parser")

        table = soup.select_one("table.wikitable")
        if not table:
            return []
        
        links = {}

       
        row_table = table.find_all("td")
        for idx, elen in enumerate(row_table):
            if idx %7 == 0:
                position = elen.text.strip()
            if idx % 7 == 1:
                monster_name = elen.text.strip()
                link_monster = elen.find("a")["href"]
                img_monster = elen.find("img")["data-src"]

                links[int(position)] = [monster_name, unquote(link_monster), img_monster]

        return links
    
    def save_links_to_csv (self):

        df = pd.DataFrame(data=self.links).T
        df.columns = ["Name_monster", "Link_monster", "Img_monster"]

        df.to_csv("links_monsters.csv", index=False, encoding="utf-8")

    
    def get_synthese_monster(self):

        link_monster = pd.read_csv("links_monsters.csv")
        column_link_monster = link_monster["Link_monster"]

        data = {}

        for idx, link in enumerate(column_link_monster[1:]):
            html = self._get_page_html_via_api(re.sub(r"^/wiki/", "", link), index=idx+1)
            soup = BeautifulSoup(html, "html.parser")

            if not soup.select_one("span#Synthesis"):
                data[idx]= {
                    "name_monster": re.sub(r"^/wiki/", "", link),
                    "parent_1" : "NONE",
                    "parent_2" : "NONE",
                    "comment": "NONE"
                }
                continue
                

            table_syn = soup.select_one("table.wikitable")

            synthese_comment = table_syn.find_all("tr")[-1].text

            parents = table_syn.find_all("td")

            parent1 = list({a.get("title") for a in parents[0].select("a[title]")})
            parent2 = list({a.get("title") for a in parents[1].select("a[title]")})
            
            parents = " + ".join([el.text.strip() for el in table_syn.find_all("td")])
           
            data[idx] = {
                "name_monster": re.sub(r"^/wiki/", "", link),
                "parent_1" : " | ".join(parent1),
                "parent_2" : " | ".join(parent2), 
                "comment": synthese_comment.strip()
            }

        return pd.DataFrame(data).T
    
    def save_synthese_to_csv(self):

        df = pd.DataFrame(self.syn_dataframe)
        print(df.shape)
        df.to_csv("Syn_mosnter.csv",  index=False, encoding="utf-8")
        
        


## update to do test 
mb = MonstersBanks()
#mb.save_links_to_csv()
#mb.get_synthese_monster()
mb.save_synthese_to_csv()