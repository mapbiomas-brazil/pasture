from ServeStatus.app import create_app
from Lapig.Functions import __login_manual
import ee
__login_manual(ee)
create_app()