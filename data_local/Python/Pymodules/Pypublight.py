#########################################
#Configurations modules for publightt   #
#                                       #
#By:Tal Potlog (tal.potlog@comverse.com #
#########################################
from Pyfiledit import builder
import copy
class publight_config(builder):
     def __call__(self, *args, **kwargs):
        from Pyfunc import publight_prx_config
        self.logger.error('Configuring ~publight/conf/config.xml')
        PublightTemplate=self.config.get('PublightTemplate')
        _=self.config.get('_')
        if _('DPI', 'type', False):
            self.logger.error('Found DPI section, going to update DPI RIP in publight XML')
        else:
            self.logger.error('No DPI section was found, skipping publight configurations')
            return
        PublightConfFile=self.config.get('PublightConfFile')
        publight_prx_config(configuration_file=PublightTemplate,Sysconfig=_,destenation_file=PublightConfFile)
