import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "./pages/NotFound.tsx";
import PrismLayout from "./components/prism/PrismLayout";
import Landing from "./pages/prism/Landing";
import Audit from "./pages/prism/Audit";
import HowItWorks from "./pages/prism/HowItWorks";
import Demo from "./pages/prism/Demo";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route element={<PrismLayout />}>
            <Route path="/" element={<Landing />} />
            <Route path="/audit" element={<Audit />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/demo" element={<Demo />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
