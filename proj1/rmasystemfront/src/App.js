import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import './App.css';
import Header from './Header';
import Footer from './Footer';
import Home from './pages/Home';
import ProductList from './pages/ProductList';
import FeatureManage from './pages/FeatureManage';
import Checkin from './pages/Checkin';
import Export from './pages/Export';
import DataVisualization from './pages/DataVisualization';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <div className="container mt-4">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/products" element={<ProductList />} />
            <Route path="/features" element={<FeatureManage />} />
            <Route path="/checkin" element={<Checkin />} />
            <Route path="/export" element={<Export />} />
            <Route path="/data-visualization" element={<DataVisualization />} />
          </Routes>
        </div>
        <Footer />
      </div>
    </Router>
  );
}

export default App;
