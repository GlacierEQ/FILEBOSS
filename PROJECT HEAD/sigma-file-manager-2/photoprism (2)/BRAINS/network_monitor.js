const { exec } = require('child_process');
const dns = require('dns');
const EventEmitter = require('events');

class NetworkMonitor extends EventEmitter {
  constructor(checkInterval = 30000) {
    super();
    this.isOnline = false;
    this.checkInterval = checkInterval;
    this.intervalId = null;
    this.lastOnlineTime = null;
    this.checkHosts = [
      'google.com',
      'microsoft.com',
      'cloudflare.com'
    ];
  }
  
  start() {
    console.log('Network monitoring started');
    this.checkConnectivity();
    this.intervalId = setInterval(() => this.checkConnectivity(), this.checkInterval);
  }
  
  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
      console.log('Network monitoring stopped');
    }
  }
  
  async checkConnectivity() {
    try {
      const wasOnline = this.isOnline;
      this.isOnline = await this.isConnected();
      
      if (this.isOnline) {
        this.lastOnlineTime = new Date();
        
        if (!wasOnline) {
          console.log('Network connection restored');
          this.emit('online');
        }
      } else if (wasOnline) {
        console.log('Network connection lost');
        this.emit('offline');
      }
      
      this.emit('statusUpdate', {
        isOnline: this.isOnline,
        lastChecked: new Date(),
        lastOnlineTime: this.lastOnlineTime
      });
      
      return this.isOnline;
    } catch (error) {
      console.error(`Error checking connectivity: ${error.message}`);
      this.isOnline = false;
      this.emit('error', error);
      return false;
    }
  }
  
  async isConnected() {
    // Try DNS resolution first (faster)
    try {
      for (const host of this.checkHosts) {
        await this.resolveDns(host);
        return true;
      }
    } catch (error) {
      // If DNS fails, try ping as fallback
      try {
        await this.ping('8.8.8.8');
        return true;
      } catch (error) {
        return false;
      }
    }
  }
  
  resolveDns(host) {
    return new Promise((resolve, reject) => {
      dns.resolve(host, (err) => {
        if (err) {
          reject(err);
        } else {
          resolve();
        }
      });
    });
  }
  
  ping(host) {
    return new Promise((resolve, reject) => {
      const command = process.platform === 'win32' 
        ? `ping -n 1 -w 1000 ${host}` 
        : `ping -c 1 -W 1 ${host}`;
      
      exec(command, (error) => {
        if (error) {
          reject(error);
        } else {
          resolve();
        }
      });
    });
  }
  
  getStatus() {
    return {
      isOnline: this.isOnline,
      lastChecked: new Date(),
      lastOnlineTime: this.lastOnlineTime
    };
  }
}

module.exports = NetworkMonitor;
