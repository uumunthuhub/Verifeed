import sys
import os
sys.path.insert(0, os.path.join(os.getcwd(), 'apps/api'))
from app.services.live_search import search_live_web_news
print(search_live_web_news("does malawi offer e Id FOR CITIZENS?"))
