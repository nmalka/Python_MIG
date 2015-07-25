
##################################
#   By: Itzik Ben Itzhak         #
#   Mail: itzik.b.i@gmail.com    #
#   Ver: 4.8                     #
#   Date: 22/06/09               #
#   ModuleNmae: Pyvcslic.py      #
##################################


from Pyfiledit import builder, filesToBakup, CopyUtils
from Pymodule import dirFix, listFilesByDate
import glob
import os, sys, string
class vrts_license(builder):
    def __call__(self):
        cp = '/bin/cp'
        vxlic = '/sbin/vxlicinst'
        backupPath = dirFix(self.config['BackupPath'])
        licDir = dirFix(self.config['LicPath']) 
        extention = self.config['Wildcard']
        src = os.path.join(licDir, extention)
        Notinuse, licFiles = listFilesByDate(licDir,extention)
        list = ', '.join(licFiles)
        if glob.glob('%s/.*' % licDir):
            File = CopyUtils(Files=list, Path=backupPath, log=self.log)	
            files = File.Backup()
            try:
                File.Delete()
            except:
                self.logger.error('Can not delete lic files:')
                self.logger.error('Going to rollback the license before exiting')
                File.RollBack()
                raise
        for lic in self.config['Lic'].split(', '):
            if os.system('%s -k %s %s' % (vxlic, lic, self.log)):
                Notinuse, licFiles = listFilesByDate(licDir,extention)
                File.Delete()
                self.logger.error('Can not add lic: %s' % lic)
                self.logger.error('Going to rollback the license before exiting')
                File.RollBack()
                raise Exception, '%107%'
