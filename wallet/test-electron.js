const { app, BrowserWindow } = require('electron');

let mainWindow;

function createWindow() {
  console.log('Creating window...');
  mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  mainWindow.loadURL('data:text/html,<h1>Test Electron Window</h1>');
  
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
  
  console.log('Window created successfully');
}

app.whenReady().then(() => {
  console.log('Electron app ready');
  createWindow();
});

app.on('window-all-closed', () => {
  console.log('All windows closed');
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

console.log('Electron script loaded');