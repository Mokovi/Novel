/**
 * Naive UI theme overrides mapped to the Writer's Atelier design tokens.
 */
export const darken = (hex, amount) => {
  const num = parseInt(hex.replace('#', ''), 16)
  const r = Math.max(0, (num >> 16) - amount)
  const g = Math.max(0, ((num >> 8) & 0x00ff) - amount)
  const b = Math.max(0, (num & 0x0000ff) - amount)
  return `rgb(${r}, ${g}, ${b})`
}

export const lightThemeOverrides = {
  common: {
    primaryColor: '#c9a94e',
    primaryColorHover: '#e0c878',
    primaryColorPressed: '#a88b3a',
    primaryColorSuppl: '#c9a94e',
    infoColor: '#6a8fbb',
    successColor: '#6aab7a',
    warningColor: '#d4a74e',
    errorColor: '#c45a5a',
    fontSize: '14px',
    fontFamily: "'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontWeightStrong: '600',
    borderRadius: '6px',
    borderColor: '#e8e0d5',
    borderRadiusSmall: '4px',
    dividerColor: '#e8e0d5',
    textColor1: '#3d3226',
    textColor2: '#5a4e40',
    textColor3: '#8a7a6a',
    bodyColor: '#faf5ed',
    cardColor: '#ffffff',
    hoverColor: 'rgba(201, 169, 78, 0.08)',
  },
  Menu: {
    itemTextColor: '#9a8e80',
    itemTextColorHover: '#ede8df',
    itemTextColorActive: '#c9a94e',
    itemIconColor: '#9a8e80',
    itemIconColorHover: '#ede8df',
    itemIconColorActive: '#c9a94e',
    itemColorActive: 'rgba(201, 169, 78, 0.12)',
    itemColorActiveHover: 'rgba(201, 169, 78, 0.18)',
    itemHeight: '44px',
    borderRadius: '6px',
    color: '#1a1614',
    borderColor: '#2a2520',
    groupTextColor: '#6a5e50',
    arrowColor: '#9a8e80',
  },
  Layout: {
    color: '#faf5ed',
    headerColor: '#1a1614',
    siderColor: '#1a1614',
    siderBorderColor: '#2a2520',
    dividerColor: '#e8e0d5',
    headerColorModal: '#1a1614',
    bodyColor: '#faf5ed',
  },
  LayoutSider: {
    borderColor: '#2a2520',
    color: '#1a1614',
  },
  Card: {
    color: '#ffffff',
    borderColor: '#e8e0d5',
    actionColor: '#faf5ed',
    borderRadiusSmall: '8px',
  },
  Button: {
    color: '#ffffff',
    colorHover: '#faf5ed',
    colorPrimary: '#c9a94e',
    colorPrimaryHover: '#d4b55e',
    colorPrimaryPressed: '#a88b3a',
    borderPrimary: '1px solid #c9a94e',
    borderHoverPrimary: '1px solid #d4b55e',
    textColorPrimary: '#ffffff',
    textColorHoverPrimary: '#ffffff',
    textColorPressedPrimary: '#ffffff',
    colorError: '#c45a5a',
    colorHoverError: '#d06a6a',
    colorPressedError: '#a84a4a',
    textColorError: '#ffffff',
    borderError: '1px solid #c45a5a',
    fontWeight: '500',
  },
  Tabs: {
    tabTextColor: '#8a7a6a',
    tabTextColorActive: '#c9a94e',
    tabTextColorHover: '#c9a94e',
    tabTextColorLine: '#8a7a6a',
    barColor: '#c9a94e',
    tabFontWeightActive: '600',
    tabBorderColor: '#e8e0d5',
  },
  Tag: {
    color: '#f0ebe3',
    colorSuccess: '#e6f4ea',
    colorWarning: '#fdf4e0',
    colorError: '#fce8e8',
    colorInfo: '#e4edf5',
    border: 'none',
    borderRadius: '4px',
  },
  Input: {
    color: '#ffffff',
    border: '1px solid #e8e0d5',
    borderHover: '1px solid #c9a94e',
    borderFocus: '1px solid #c9a94e',
    boxShadowFocus: '0 0 0 2px rgba(201, 169, 78, 0.15)',
    textColor: '#3d3226',
    placeholderColor: '#b5a99a',
  },
  Select: {
    menuColor: '#ffffff',
    menuBorderColor: '#e8e0d5',
    actionColor: '#faf5ed',
    actionTextColor: '#3d3226',
  },
  Modal: {
    color: '#ffffff',
    boxShadow: '0 8px 32px rgba(26, 22, 20, 0.18)',
  },
  Divider: {
    color: '#e8e0d5',
  },
  Popover: {
    color: '#ffffff',
    boxShadow: '0 4px 16px rgba(26, 22, 20, 0.14)',
    border: '1px solid #e8e0d5',
  },
  Notification: {
    color: '#ffffff',
    boxShadow: '0 4px 16px rgba(26, 22, 20, 0.14)',
  },
  Message: {
    color: '#ffffff',
    boxShadow: '0 4px 16px rgba(26, 22, 20, 0.14)',
  },
  Collapse: {
    titleTextColor: '#3d3226',
    titleTextColorActive: '#3d3226',
    titlePadding: '12px 16px',
    dividerColor: '#e8e0d5',
    arrowColor: '#8a7a6a',
  },
  List: {
    color: '#ffffff',
    borderColor: '#e8e0d5',
    borderRadius: '8px',
  },
  Thing: {
    titleTextColor: '#3d3226',
    descriptionTextColor: '#8a7a6a',
  },
  Tooltip: {
    color: '#3d3226',
    textColor: '#ede8df',
  },
  Switch: {
    railColorActive: '#c9a94e',
  },
  Progress: {
    railColor: '#e8e0d5',
    color: '#c9a94e',
  },
  Empty: {
    textColor: '#8a7a6a',
    iconColor: '#b5a99a',
  },
  Table: {
    tdColor: '#ffffff',
    thColor: '#faf5ed',
    borderColor: '#e8e0d5',
    thTextColor: '#3d3226',
  },
  Dialog: {
    color: '#ffffff',
    boxShadow: '0 8px 32px rgba(26, 22, 20, 0.18)',
  },
  DatePicker: {
    panelColor: '#ffffff',
  },
}
