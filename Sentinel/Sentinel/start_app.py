from ServeStatus.app import create_app
from Lapig.Functions import __login_manual, login_gee
import ee
from dynaconf import settings


if settings.IS_LOGIN_MANUAL == True:
    __login_manual()
else:
    login_gee
create_app()