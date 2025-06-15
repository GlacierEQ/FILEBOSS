import os
import sys
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import subprocess
import time
from pathlib import Path

class SortingHatWindowsService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SortingHatService"
    _svc_display_name_ = "Sorting Hat File Organization Service"
    _svc_description_ = "Automatically organizes files using AI-powered sorting"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.stop_requested = False
        self.service_process = None
        
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.stop_requested = True
        
        # Kill the service manager subprocess if it's running
        if self.service_process:
            try:
                self.service_process.terminate()
            except:
                pass
                
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        # Path to the service_manager.py script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        service_script = os.path.join(base_dir, "service_manager.py")
        
        # Start the service manager as a subprocess
        self.service_process = subprocess.Popen(
            [sys.executable, service_script],
            cwd=base_dir
        )
        
        # Wait for service to be stopped
        while not self.stop_requested:
            # Check if the service manager process is still running
            if self.service_process.poll() is not None:
                # Restart if it crashed
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_WARNING_TYPE,
                    servicemanager.PYS_SERVICE_STARTED,
                    (self._svc_name_, "Service manager stopped unexpectedly. Restarting...")
                )
                self.service_process = subprocess.Popen(
                    [sys.executable, service_script],
                    cwd=base_dir
                )
            
            # Wait for stop signal or timeout
            rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)  # 5 seconds
            if rc == win32event.WAIT_OBJECT_0:
                break
                
        # Clean up on exit
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )

if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(SortingHatWindowsService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(SortingHatWindowsService)
