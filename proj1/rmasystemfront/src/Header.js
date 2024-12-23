import React, { useState } from 'react';
import { AppstoreOutlined, MailOutlined, SettingOutlined } from '@ant-design/icons';
import { Menu } from 'antd';
import { Link } from 'react-router-dom';
import 'antd/dist/reset.css'; // Import Ant Design reset styles
import './Header.css'; // Import custom styles

const items = [
  {
    label: <Link to="/">Home</Link>,
    key: 'home',
    icon: <MailOutlined />,
  },
  {
    label: <Link to="/products">Product List</Link>,
    key: 'products',
    icon: <AppstoreOutlined />,
  },
  {
    label: <Link to="/features">Feature Manage</Link>,
    key: 'features',
    icon: <SettingOutlined />,
  },
  {
    label: <Link to="/checkin">Checkin</Link>,
    key: 'checkin',
    icon: <SettingOutlined />,
  },
  {
    label: <Link to="/export">Export</Link>,
    key: 'export',
    icon: <SettingOutlined />,
  },
  {
    label: <Link to="/data-visualization">Data Visualization and Analysis</Link>,
    key: 'data-visualization',
    icon: <SettingOutlined />,
  },
];

const Header = () => {
  const [current, setCurrent] = useState('home');

  const onClick = (e) => {
    setCurrent(e.key);
  };

  return (
    <div className="header-container">
      <div className="system-name">FXSJ RMA System</div>
      <Menu onClick={onClick} selectedKeys={[current]} mode="horizontal" items={items} />
    </div>
  );
};

export default Header;