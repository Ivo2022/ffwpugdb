from core.models.donation import Donation, DonationType
from core.crud.base import CRUDBase

donation_crud = CRUDBase(Donation)
