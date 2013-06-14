# -*- coding: utf-8 -*-

import time
from logging.handlers import TimedRotatingFileHandler
from logging.handlers import BaseRotatingHandler
import os

class MultiProcessRotatingFileHandler(TimedRotatingFileHandler):
    """
    handler for logging to a file for multi process...
    """

    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False):
        TimedRotatingFileHandler.__init__(self, filename, when, interval, backupCount, encoding, delay, utc)
        self.lastRolloverAt = 0
        if not os.path.exists(self.baseFilename):
            self.dev, self.ino = -1, -1
        else:
            stat = os.stat(self.baseFilename)
            self.dev, self.ino = stat.st_dev, stat.st_ino

    def emit(self, record):
        """
        Emit a record.

        First check if the underlying file has changed between the given time, and if it
        has, close the old stream and reopen the file to get the
        current stream.
        """
        current_time = int(time.time())
        if current_time > self.lastRolloverAt and current_time < self.lastRolloverAt + 600:
            if not os.path.exists(self.baseFilename):
                stat = None
                changed = 1
            else:
                stat = os.stat(self.baseFilename)
                changed = (stat.st_dev != self.dev) or (stat.st_ino != self.ino)
            if changed and self.stream is not None:
                self.stream.flush()
                self.stream.close()
                self.stream = self._open()
                if stat is None:
                    stat = os.stat(self.baseFilename)
                self.dev, self.ino = stat.st_dev, stat.st_ino
        BaseRotatingHandler.emit(self, record)
        
    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        #here we do not remove the dfn simply, we should guess it.
        if os.path.exists(dfn):
            stat = os.stat(dfn)
            last_mt = int(stat.st_mtime)
            current_time = int(time.time())
            if last_mt + 3600 < current_time:
                os.remove(dfn)
                os.rename(self.baseFilename, dfn)
        else:
            try:
                os.rename(self.baseFilename, dfn)
            except:
                #TODO, fix it
                pass
        if self.backupCount > 0:
            # find the oldest log file and delete it
            #s = glob.glob(self.baseFilename + ".20*")
            #if len(s) > self.backupCount:
            #    s.sort()
            #    os.remove(s[0])
            for s in self.getFilesToDelete():
                os.remove(s)
        #print "%s -> %s" % (self.baseFilename, dfn)
        #self.mode = 'w'
        self.stream = self._open()
        currentTime = int(time.time())
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        #If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstNow = time.localtime(currentTime)[-1]
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    newRolloverAt = newRolloverAt - 3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    newRolloverAt = newRolloverAt + 3600
        self.lastRolloverAt = self.rolloverAt
        self.rolloverAt = newRolloverAt
