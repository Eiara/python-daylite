import requests
from requests_oauthlib import OAuth2Session
from urllib.parse import urljoin
from .models import DayliteData, Contact, Thin_Contact

USER_AUTHORISE_URL="https://www.marketcircle.com/account/oauth/authorize"
OAUTH_TOKEN_URL="https://www.marketcircle.com/account/oauth/token"

AUTH_URL = "https://api.marketcircle.net/v1"
URL_ROOT = "https://api.marketcircle.net/"


class Daylite:
    
    def __init__(self, client_id, token):
        _token = {"access_token": token}
        self.session = OAuth2Session(client_id, token=_token)
    
    def check_session(self) -> int:
        res = self.session.get(AUTH_URL)
        return res.status_code == 200
        
    def fetch(self, schema, ref) -> DayliteData:
        res = self.session.get(urljoin(URL_ROOT, ref))
        res.raise_for_status()
        return DayliteData._server(schema, res.json(), self)
    
    def contacts(self) -> [DayliteData]:
        """
        Returns a list of all contacts,
        in the "tiny contacts" variant.
        """
        res = self.session.get(urljoin(URL_ROOT, "/v1/contacts"))
        res.raise_for_status()
        body = res.json()
        # Thin_Contact doesn't have the normal server-provided
        # values in it
        # And shouldn't be used commonly anyway
        return [DayliteData(Thin_Contact, row) for row in body]
    
    def contact(self, id_) -> DayliteData:
        return self.fetch(Contact, id_)
    
    def companies(self) -> [DayliteData]:
        """
        Returns a list of all contacts,
        in the "tiny contacts" variant.
        """
        res = self.session.get(urljoin(URL_ROOT, "/v1/companies"))
        res.raise_for_status()
        body = res.json()
        return [DayliteData(Company, row) for row in body]
    
    def company(self, id_):
        pass
        # return self.fetch(Company, id_)
    
    def opportunity(self, id_):
        pass
        # return self.fetch(Opportunity, id_)
        
    def project(self):
        
        pass
    
    def resource(self):
        pass
        
    def appointment(self):
        pass
        
    def task(self):
        pass
        
    def user(self):
        pass
        
    def note(self):
        
        pass
        
    def form(self):
        
        pass
        
    def group(self):
        
        pass
        
    def subscription(self):
        
        pass
        
    