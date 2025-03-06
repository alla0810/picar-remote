const { app, BrowserWindow } = require('electron')
const path = require('path')

function createWindow () {
  // Create the browser window
  const mainWindow = new BrowserWindow({
    width: 1000,
    height: 700,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      preload: path.join(__dirname, 'preload.js')
    }
  })

  // Load the index.html file
  mainWindow.loadFile('index.html')
  
  // Set focus to the window to make keyboard shortcuts work
  mainWindow.on('ready-to-show', () => {
    mainWindow.focus();
  });
  
  // Optional: Open DevTools for debugging
  // mainWindow.webContents.openDevTools()
}

// When Electron is ready, create the window
app.whenReady().then(() => {
  createWindow()
  
  app.on('activate', function () {
    if (BrowserWindow.getAllWindows().length === 0) createWindow()
  })
})

// Quit when all windows are closed, except on macOS
app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit()
})