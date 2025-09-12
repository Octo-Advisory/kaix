// components/ErrorBoundary.jsx
import React from 'react';
import { useDispatch } from 'react-redux';
import { setFormData, setIsOpen } from '../../Redux/Store/Featuresilces/detailform';
import FailureScreen from '../Failure/FailureScreen';
import { useFrappeCreateDoc } from 'frappe-react-sdk';

class ErrorBoundaryClass extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.props.onError?.(error, errorInfo);
  }

  render() {

    // return this.state.hasError ? null : this.props.children;
    return this.state.hasError ? <FailureScreen /> : this.props.children;
  }
}

export default function ErrorBoundary({ children }) {
  const { createDoc } = useFrappeCreateDoc('');
  const createDiagnostic = (errType, logMsg,chatId)=> {
      let log = ` ${logMsg}`
      createDoc("AIX Diagnostics Hub", {
      type: errType,
      note: log,
      chat_name: chatId
      });
  }
  const dispatch = useDispatch();
  const handleError = (error, errorInfo) => {
    dispatch(setFormData({ description: error.message }));
    dispatch(setIsOpen(true));
      createDiagnostic("Others", `Error From Error Boundary : ${JSON.stringify(errorInfo)} ${JSON.stringify(error)}`,'')
    // console.error("Caught by Error Boundary:", error, errorInfo);
  };

  return <ErrorBoundaryClass onError={handleError}>{children}</ErrorBoundaryClass>;
}
