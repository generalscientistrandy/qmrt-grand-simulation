import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import { Layout } from "@/components/Layout";
import { QMRTSimulationLab } from "@/components/QMRTSimulationLab";
import LongPathDynamics from "@/components/LongPathDynamics";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<QMRTSimulationLab />} />
            <Route path="/longpath" element={<LongPathDynamics />} />
          </Routes>
        </Layout>
      </BrowserRouter>
      <Toaster position="top-right" theme="dark" />
    </div>
  );
}

export default App;
