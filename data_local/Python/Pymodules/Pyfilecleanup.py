
######################################
#   By: Netanel Malka                #
#   Mail: Netanel.Malka@comverse.com #
#   ModuleName: Pycleanup.py         #
######################################


from Pyfiledit import builder
import os, re ,sys
from glob import glob
from pdb import set_trace as st
 
class clean_set_file(builder):

    def __init__(self, config, loggerName='', *args, **kwargs):
        super(clean_set_file, self).__init__(config=config, loggerName=loggerName, *args, **kwargs)
        self.set_src_path = self.config.get('SetSrcPath')
        self.set_dst_path = self.config.get('SetDstPath')
        self.clean_src_path = self.config.get('CleanSrcPath')
        self.clean_dst_path = self.config.get('CleanDstPath')
        self.app_file_prefix = self.config.get('FilePrefix', '') 
        self.app_file_suffix = self.config.get('FileSuffix', '') 

        self.ignored_suffix = self.config.get('IgnoredSuffix')
        self.selected_apps = [ app.upper() for app in self.config.get('SelectedApps', []) ]
        self.ignored_apps = [ app.upper() for app in self.config.get('IgnoredApps', []) ]  
        self.ignored_files = self.config.get('IgnoredFiles', [])
        self.delimiter = self.config.get('IgnoredSuffixDelimiter', '.')
        self.all = self.config.get('SetCleanAll', 'no').lower() == 'yes' and True or False

        if self.ignored_suffix:
            if not re.search('^[a-zA-Z0-9_-]+$', self.ignored_suffix):
                raise Exception, '"IgnoreSuffix" value can be: alphanumeric or _ or -' 
        else:
            self.delimiter = ''
  
        self.logger.debug('IgnoreSuffix = "%s"' % self.ignored_suffix)
        self.logger.debug('Delimiter = "%s"' % self.delimiter)
        self.logger.debug('SetSrcPath = "%s"' % self.set_src_path)
        self.logger.debug('SetDstPath = "%s"' % self.set_dst_path)
        self.logger.debug('CleanSrcPath = "%s"' % self.clean_src_path)
        self.logger.debug('CleanDstPath = "%s"' % self.clean_dst_path)
        self.logger.debug('FilePrefix = "%s"' % self.app_file_prefix)
        self.logger.debug('FileSuffix = "%s"' % self.app_file_suffix)
        self.logger.debug('SelectedApps = "%s"' % self.selected_apps)
        self.logger.debug('IgnoredApps = "%s"' % self.ignored_apps)
        self.logger.debug('IgnoredFiles = "%s"\n\n' % self.ignored_files)
        

    def set(self):
        self.logger.error('###### Set Start ######\n\n')

        if not self.delimiter:
            if self.set_src_path == self.set_dst_path:
                raise Exception, '"IgnoreSuffix" can\'t be empty when SetSrcPath "%s" and SetDstPath %s are equal!!!.' % \
                                   (self.set_src_path, self.set_dst_path)

        self.apps_files = [f.split('/')[-1] for f in glob(os.path.join(self.set_src_path, '%s*%s*' % \
                          (self.app_file_prefix, self.app_file_suffix ))) if os.path.isfile(f)]

        app_file_regex = ('^%s(.*)%s%s%s') % (self.app_file_prefix, self.app_file_suffix, self.delimiter and '\\%s' % \
                                              self.delimiter or '', self.ignored_suffix)
        self.logger.debug('Set app_file_regex = "%s"' % app_file_regex)

        for app_file in self.apps_files:
            reg_obj = re.search(app_file_regex, app_file)
            if reg_obj:
                app_name = reg_obj.groups(0)[0]
                file_name = '%s%s%s' % (self.app_file_prefix, app_name, self.app_file_suffix)
                if (not self.all and app_name.upper() in self.selected_apps) or self.all:
                    old_file_name = os.path.join(self.set_src_path, file_name + '%s%s' % (self.delimiter, self.ignored_suffix))
                    new_file_name = os.path.join(self.set_dst_path, file_name)
                    self.rename_file(old_file_name, new_file_name)
                    self.logger.error('Successfully rename file from %s to %s' % (old_file_name, new_file_name))
                else:
                    self.logger.debug('Skipping rename for "%s" file.' % os.path.join(self.set_src_path ,file_name))
            
        self.logger.error('###### Set End ######\n\n')
            
    def unset(self):
        self.logger.error('###### Clean Start ######\n\n')

        if not self.delimiter:
            if self.clean_src_path == self.clean_dst_path:
                raise Exception, '"IgnoreSuffix" can\'t be empty when CleanSrcPath "%s" and CleanDstPath %s are equal!!!.' % \
                                   (self.clean_src_path, self.clean_dst_path)

        self.apps_files = [f.split('/')[-1] for f in glob(os.path.join(self.clean_src_path, '%s*%s' % \
                          (self.app_file_prefix, self.app_file_suffix ))) if os.path.isfile(f)]

        app_file_regex = '^%s(.*)%s$' % (self.app_file_prefix, self.app_file_suffix)
        self.logger.debug('Clean app_file_regex = "%s"' % app_file_regex)
        for app_file in self.apps_files:
            reg_obj = re.search(app_file_regex, app_file)
            if reg_obj:
                 app_name = reg_obj.groups(0)[0]
                 if app_name.upper() not in self.ignored_apps and app_file not in self.ignored_files: 
                     old_file_name = os.path.join(self.clean_src_path, app_file)
                     new_file_name = os.path.join(self.clean_dst_path, app_file + '%s%s' % (self.delimiter, self.ignored_suffix))
                     self.rename_file(old_file_name, new_file_name)
                     self.logger.error('Successfully rename file from %s to %s' % (old_file_name, new_file_name))
                 else:
                     self.logger.debug('Skipping rename for "%s" file.' % os.path.join(self.clean_src_path ,app_file))

        self.logger.error('###### Clean End ######\n\n')
     
    def rename_file(self, old_file, new_file):
        try:
            os.rename(old_file, new_file)
        except:
            self.logger.error('Couln\'t rename file from %s to %s.' % (old_file, new_file))
            raise Exception, 'Couln\'t rename file %s to %s.' % (old_file, new_file)


class file_setup(clean_set_file):
    def __call__(self, *args, **kwargs):
        self.set()
 
class file_clean(clean_set_file):
    def __call__(self, *args, **kwargs):
        self.unset()

class file_cleansetup(clean_set_file):
    def __call__(self, *args, **kwargs):
        self.unset()
        self.set()
