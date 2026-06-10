import React, { createContext, useContext, useReducer } from "react";

const initialState = {
  file: null,
};

const StateContext = createContext({ state: initialState, dispatch: null });

const stateReducer = (state: any, action: any) => {
  switch (action.type) {
    case "SET_FILE":
      return {
        ...state,
        file: action.payload,
      };
    default:
      return state;
  }
};

export const StateProvider = ({ children }) => {
  const [state, dispatch] = useReducer(stateReducer, initialState);

  return (
    <StateContext.Provider value={{ state, dispatch }}>
      {children}
    </StateContext.Provider>
  );
};

export const useStateContext = () => useContext(StateContext);
