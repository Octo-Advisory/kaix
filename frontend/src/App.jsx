import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Home from './components/Home/Home';
import Solution from './components/Solution/Solution';
import ProgressScreen from './components/ProgressScreen/ProgressScreen'
import TestComponent from './components/TestComponent/TestComponent';
import Test from './components/TestComponent/Test';
import Solutionscreen from './components/SolutionScreen/Solutionscreen';
import MapComponent from './components/MapComponent/MapComponent';
import Login from './components/Login/Login';
import Signup from './components/Signup/Signup';
import Chatscreen from './components/Chatscreen/Chatscreen';
import { useFrappeAuth } from "frappe-react-sdk";
import ForgotPassword from './components/ForgotPassword/ForgotPassword';
import Temp from './components/Home/Temp';
import Details from './components/Details/Details';
import Renderresult from './components/Rerenderresult/Renderresult';
import Propertycreation from './components/Propertycreation/Propertycreation';
import ErrorBoundary from './components/ErrorBoundary/ErrorBoundary';
import NoResultsFound from './components/Failure/NoResultsFound';

const PrivateRoute = () => {
  const { currentUser, isValidating } = useFrappeAuth();
  if (isValidating) return <div>Loading...</div>;
  return currentUser ? <Outlet /> : <Navigate to="/login" replace />;
};

function App() {

  const { currentUser } = useFrappeAuth();
  return (
    <>
      <BrowserRouter basename="/frontend">
      {/* <ErrorBoundary> */}
        <Routes>
          {/* Redirect root path to /login */}
          <Route path="/" element={<Navigate to={currentUser ? "/chat" : "/login"} replace />} />

          {/* Login and Signup */}
          <Route path="/login" element={currentUser ? <Navigate to="/chat" replace /> : <Login />} />
          <Route path="/signup" element={currentUser ? <Navigate to="/chat" replace /> : <Signup />} />

          {/* Chat routes */}
          <Route path="/chat" element={<Chatscreen />} />
          <Route path="/chat/:sessionId" element={<Chatscreen />} />

          {/* Other routes */}
          <Route path="/temp" element={<Temp />} />
          <Route path="/progress" element={<ProgressScreen />} />
          <Route path="/progress/:sessionId" element={<ProgressScreen />} />
          <Route path="/solution" element={<Solutionscreen />} />
          <Route path="/build" element={<TestComponent />} />
          {/* <Route path="/test" element={<Test />} /> */}
          <Route path="/test" element={<NoResultsFound />} />
          <Route path="/map" element={<MapComponent />} />
          <Route path="/forgotpassword" element={<ForgotPassword />} />
          <Route path="/result" element={<Renderresult />} />
          <Route path="/property" element={<Propertycreation />} />
        </Routes>
        {/* </ErrorBoundary> */}
      </BrowserRouter>
      
      <Details />
    </>
  );
}

export default App;