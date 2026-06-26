import React, { createContext, useContext, useReducer } from 'react';

// Initial state
const initialState = {
  scanResults: [],
  currentScan: null,
  isLoading: false,
  error: null,
  scanHistory: [],
  complianceRules: [],
  apiStatus: null,
};

// Action types
export const actionTypes = {
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  SET_CURRENT_SCAN: 'SET_CURRENT_SCAN',
  ADD_SCAN_RESULT: 'ADD_SCAN_RESULT',
  SET_SCAN_HISTORY: 'SET_SCAN_HISTORY',
  SET_COMPLIANCE_RULES: 'SET_COMPLIANCE_RULES',
  SET_API_STATUS: 'SET_API_STATUS',
  CLEAR_ERROR: 'CLEAR_ERROR',
};

// Reducer
const appReducer = (state, action) => {
  switch (action.type) {
    case actionTypes.SET_LOADING:
      return {
        ...state,
        isLoading: action.payload,
      };
    case actionTypes.SET_ERROR:
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };
    case actionTypes.SET_CURRENT_SCAN:
      return {
        ...state,
        currentScan: action.payload,
        isLoading: false,
      };
    case actionTypes.ADD_SCAN_RESULT:
      return {
        ...state,
        scanResults: [action.payload, ...state.scanResults],
        currentScan: action.payload,
        isLoading: false,
      };
    case actionTypes.SET_SCAN_HISTORY:
      return {
        ...state,
        scanHistory: action.payload,
      };
    case actionTypes.SET_COMPLIANCE_RULES:
      return {
        ...state,
        complianceRules: action.payload,
      };
    case actionTypes.SET_API_STATUS:
      return {
        ...state,
        apiStatus: action.payload,
      };
    case actionTypes.CLEAR_ERROR:
      return {
        ...state,
        error: null,
      };
    default:
      return state;
  }
};

// Create context
const AppContext = createContext();

// Context provider
export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Action creators
  const setLoading = (isLoading) => {
    dispatch({ type: actionTypes.SET_LOADING, payload: isLoading });
  };

  const setError = (error) => {
    dispatch({ type: actionTypes.SET_ERROR, payload: error });
  };

  const clearError = () => {
    dispatch({ type: actionTypes.CLEAR_ERROR });
  };

  const setCurrentScan = (scan) => {
    dispatch({ type: actionTypes.SET_CURRENT_SCAN, payload: scan });
  };

  const addScanResult = (result) => {
    dispatch({ type: actionTypes.ADD_SCAN_RESULT, payload: result });
  };

  const setScanHistory = (history) => {
    dispatch({ type: actionTypes.SET_SCAN_HISTORY, payload: history });
  };

  const setComplianceRules = (rules) => {
    dispatch({ type: actionTypes.SET_COMPLIANCE_RULES, payload: rules });
  };

  const setApiStatus = (status) => {
    dispatch({ type: actionTypes.SET_API_STATUS, payload: status });
  };

  const value = {
    ...state,
    setLoading,
    setError,
    clearError,
    setCurrentScan,
    addScanResult,
    setScanHistory,
    setComplianceRules,
    setApiStatus,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

// Custom hook to use the context
export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

export default AppContext;
