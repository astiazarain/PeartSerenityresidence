import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './pages/Home';
import Services from './pages/Services';
import About from './pages/About';
import Facility from './pages/Facility';
import Contact from './pages/Contact';
import Auth from './pages/Auth';
import QuoteRequest from './pages/QuoteRequest';
import Dashboard from './pages/Dashboard';
import Careers from './pages/Careers';
import Gallery from './pages/Gallery';
import FAQ from './pages/FAQ';
import Terms from './pages/Terms';
import Privacy from './pages/Privacy';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Home />} />
          <Route path="/services" element={<Services />} />
          <Route path="/about" element={<About />} />
          <Route path="/facility" element={<Facility />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/quote" element={<QuoteRequest />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/careers" element={<Careers />} />
          <Route path="/gallery" element={<Gallery />} />
          <Route path="/faq" element={<FAQ />} />
          <Route path="/terms" element={<Terms />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="*" element={<Home />} />
        </Route>
        <Route path="/auth" element={<Auth />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
