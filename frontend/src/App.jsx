import './App.css';
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from './components/Home/Home';
import Solution from './components/Solution/Solution';
import ProgressScreen from './components/ProgressScreen/ProgressScreen'
import TestComponent from './components/TestComponent/TestComponent';
import Test from './components/TestComponent/Test';
import Solutionscreen from './components/SolutionScreen/Solutionscreen';

function App() {
  return (
    <BrowserRouter basename="/frontend">
      <Routes>
        <Route path="/" element={<Home />} />
        {/* <Route path="solution" element={<Solution />} /> */}
        <Route path="/progress" element={<ProgressScreen />} />
        <Route path="/solution" element={<Solutionscreen />} />
        <Route path="/build" element={<TestComponent />} />
        <Route path="/test" element={<Test />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;