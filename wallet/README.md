# PlayerGold Wallet

Cartera de escritorio oficial para PlayerGold ($PRGLD) - Hecho por gamers para gamers, totalmente libre, democrático y sin censura.

## Características

- 🔒 **Seguridad**: Generación segura de claves criptográficas y frases de recuperación
- 💰 **Gestión de Tokens**: Envío, recepción y gestión de tokens PlayerGold ($PRGLD)
- ⛏️ **Minería Integrada**: Convierte tu cartera en un nodo minero con IA local
- 🌐 **Multiplataforma**: Compatible con Windows, macOS y Linux
- 🎮 **Gaming Focus**: Diseñado específicamente para la comunidad gaming
- 🤖 **Consenso PoAIP**: Participación en el consenso gestionado por IA

## Instalación

### Requisitos del Sistema

- **Sistema Operativo**: Windows 10+, macOS 10.14+, o Linux (Ubuntu 18.04+)
- **RAM**: Mínimo 4GB (8GB recomendado para minería)
- **Almacenamiento**: 500MB de espacio libre
- **Para Minería**: GPU con 4GB+ VRAM, CPU 4+ cores

### Instalación desde Código Fuente

1. Clona el repositorio:
```bash
git clone https://github.com/playergold/wallet-desktop.git
cd wallet-desktop
```

2. Instala las dependencias:
```bash
npm install
```

3. Ejecuta en modo desarrollo:
```bash
npm run dev
```

4. Construye para producción:
```bash
npm run build
npm run electron-build
```

## Uso

### Primera Configuración

1. **Crear Nueva Cartera**: Genera una nueva cartera con frase de recuperación de 12 palabras
2. **Importar Cartera**: Importa una cartera existente usando tu frase de recuperación
3. **Configurar Seguridad**: Configura PIN y autenticación de dos factores (opcional)

### Funcionalidades Principales

#### Gestión de Carteras
- Crear múltiples carteras
- Importar/exportar carteras
- Cambiar entre carteras
- Gestión de nombres y etiquetas

#### Transacciones
- Enviar tokens PlayerGold ($PRGLD)
- Recibir tokens con código QR
- Historial completo de transacciones
- Tracking de confirmaciones en tiempo real

#### Minería con IA
- Descarga automática de modelos IA certificados
- Monitoreo de estado del nodo
- Estadísticas de recompensas
- Control de inicio/parada de minería

#### Seguridad
- Almacenamiento encriptado local
- Autenticación de dos factores (2FA)
- PIN de acceso
- Detección de actividad sospechosa

## Arquitectura Técnica

### Stack Tecnológico
- **Frontend**: React 18 + Electron
- **Backend**: Node.js con servicios nativos
- **Criptografía**: secp256k1, bip39, hdkey
- **Almacenamiento**: electron-store (encriptado)
- **Red**: Conexión P2P con nodos PlayerGold

### Estructura del Proyecto
```
wallet/
├── src/
│   ├── main.js              # Proceso principal de Electron
│   ├── preload.js           # Script de preload seguro
│   ├── App.js               # Componente principal React
│   ├── components/          # Componentes React
│   └── services/            # Servicios de backend
├── public/                  # Archivos públicos
├── build/                   # Build de producción
└── dist/                    # Distribución final
```

### Seguridad

#### Almacenamiento Seguro
- Las claves privadas se almacenan encriptadas localmente
- Las frases de recuperación se encriptan con AES-256
- Nunca se envían datos sensibles a servidores externos

#### Comunicación Segura
- Todas las comunicaciones P2P usan TLS 1.3
- Firmas criptográficas para todas las transacciones
- Verificación de integridad de modelos IA por hash

## Desarrollo

### Scripts Disponibles

```bash
npm start          # Ejecutar Electron en producción
npm run dev        # Desarrollo con hot reload
npm run build      # Construir aplicación React
npm run electron-build  # Construir aplicación Electron
npm run dist       # Crear distribución para todas las plataformas
npm test           # Ejecutar tests
```

### Estructura de Componentes

- **App.js**: Componente raíz con routing
- **WalletSetup.js**: Configuración inicial de carteras
- **Dashboard.js**: Panel principal con navegación
- **WalletOverview.js**: Resumen de cartera y estadísticas
- **WalletManager.js**: Gestión de múltiples carteras
- **CreateWallet.js**: Creación de nuevas carteras
- **ImportWallet.js**: Importación de carteras existentes

### API de Servicios

#### WalletService
- `generateWallet()`: Genera nueva cartera
- `importWallet(mnemonic)`: Importa cartera existente
- `exportWallet(walletId)`: Exporta frase de recuperación
- `getWallets()`: Lista todas las carteras

## Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## Soporte

- **Documentación**: [docs.playergold.com](https://docs.playergold.com)
- **Discord**: [discord.gg/playergold](https://discord.gg/playergold)
- **Issues**: [GitHub Issues](https://github.com/playergold/wallet-desktop/issues)
- **Email**: support@playergold.com

## Roadmap

### v1.0 (Actual)
- ✅ Gestión básica de carteras
- ✅ Interfaz de usuario completa
- ✅ Seguridad y encriptación

### v1.1 (Próximo)
- 🔄 Funcionalidades de transacciones
- 🔄 Sincronización con red PlayerGold
- 🔄 Historial de transacciones

### v1.2 (Futuro)
- ⏳ Minería integrada con IA
- ⏳ Staking y DeFi
- ⏳ Integración con juegos

---

**PlayerGold** - Hecho por gamers para gamers, totalmente libre, democrático y sin censura.