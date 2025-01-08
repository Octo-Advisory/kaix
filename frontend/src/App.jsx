import './App.css';
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from './components/Home/Home';
import Solution from './components/Solution/Solution';
import ProgressScreen from './components/ProgressScreen/ProgressScreen'


function App() {
  return (
    <BrowserRouter basename="/frontend">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="solution" element={<Solution />} />
        <Route path="progress" element={<ProgressScreen />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;