!include "MUI2.nsh"
!include "FileFunc.nsh"
!include "TextFunc.nsh"

Name "LS Imagecomm"
Caption "LS Imagecomm | Redimensionar e Remover Fundo"
OutFile "dist\LS Imagecomm Setup.exe"
Unicode True
RequestExecutionLevel admin
SetCompressor /SOLID lzma
SetDatablockOptimize On
BrandingText "LS Imagecomm"

!define PRODUCT "LS Imagecomm"
!define VERSION "1.3.0"
!define PUBLISHER "LS Imagecomm"
!define EXE "Redimensionar Imagens.exe"
!define ICO "src\redimensionar\app_icon.ico"

Var StartMenuFolder

InstallDir "$PROGRAMFILES64\${PRODUCT}"
InstallDirRegKey HKLM "Software\${PRODUCT}" "InstallDir"

!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${EXE}"
!define MUI_FINISHPAGE_RUN_TEXT "Executar ${PRODUCT}"
!define MUI_ICON "${ICO}"
!define MUI_UNICON "${ICO}"
!define MUI_COMPONENTSPAGE_SMALLDESC

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "Portuguese"
!insertmacro MUI_LANGUAGE "English"

Section "Aplicação" SecApp
  SectionIn RO

  SetOutPath "$INSTDIR"

  File "dist\${EXE}"
  File "${ICO}"

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  WriteRegStr HKLM "Software\${PRODUCT}" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" \
    "DisplayName" "${PRODUCT}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" \
    "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" \
    "DisplayIcon" "$INSTDIR\${EXE},0"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" \
    "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" \
    "Publisher" "${PUBLISHER}"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" \
    "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" \
    "NoRepair" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}" \
    "EstimatedSize" 155000
SectionEnd

Section "Atalhos" SecShortcuts
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\${PRODUCT}.lnk" \
      "$INSTDIR\${EXE}" "" "$INSTDIR\${EXE}" 0
    CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Desinstalar ${PRODUCT}.lnk" \
      "$INSTDIR\Uninstall.exe"
    CreateShortCut "$DESKTOP\${PRODUCT}.lnk" \
      "$INSTDIR\${EXE}" "" "$INSTDIR\${EXE}" 0
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section "Uninstall"
  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder

  Delete "$DESKTOP\${PRODUCT}.lnk"
  RMDir /r "$SMPROGRAMS\$StartMenuFolder"

  Delete "$INSTDIR\${EXE}"
  Delete "$INSTDIR\${ICO}"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"

  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT}"
  DeleteRegKey HKLM "Software\${PRODUCT}"
SectionEnd
