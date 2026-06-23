// React Context for global state (currently only to pass image file between pages)

import {
  ActionDispatch,
  createContext,
  FC,
  JSX,
  PropsWithChildren,
  useContext,
  useReducer,
} from "react";

type GlobalState = {
  file: File | null;
};

type StateContextValue = {
  state: GlobalState;
  dispatch: ActionDispatch<any> | null;
};

const initialState = {
  file: null,
};

const StateContext = createContext<StateContextValue>({
  state: initialState,
  dispatch: null,
});

const stateReducer = (state: GlobalState, action: any) => {
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

export const StateProvider: FC<PropsWithChildren> = ({
  children,
}): JSX.Element => {
  const [state, dispatch] = useReducer(stateReducer, initialState);

  return (
    <StateContext.Provider value={{ state, dispatch }}>
      {children}
    </StateContext.Provider>
  );
};

export const useStateContext = () => useContext(StateContext);
