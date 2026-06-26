import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { FiHome, FiSearch, FiList, FiShield, FiMenu, FiX, FiActivity } from 'react-icons/fi';

const NavbarContainer = styled.nav`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #e2e8f0;
  z-index: 1000;
  padding: 0 2rem;
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;

  @media (max-width: 768px) {
    padding: 0 1rem;
  }
`;

const Logo = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  text-decoration: none;

  .icon {
    color: #3b82f6;
  }
`;

const NavLinks = styled.div`
  display: flex;
  align-items: center;
  gap: 2rem;

  @media (max-width: 768px) {
    display: ${props => props.isOpen ? 'flex' : 'none'};
    position: absolute;
    top: 70px;
    left: 0;
    right: 0;
    background: white;
    flex-direction: column;
    padding: 1rem;
    border-bottom: 1px solid #e2e8f0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }
`;

const NavLink = styled(Link)`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  text-decoration: none;
  color: ${props => props.isActive ? '#3b82f6' : '#64748b'};
  background: ${props => props.isActive ? '#eff6ff' : 'transparent'};
  font-weight: 500;
  transition: all 0.2s ease;

  &:hover {
    color: #3b82f6;
    background: #f8fafc;
  }

  .icon {
    font-size: 1.1rem;
  }

  @media (max-width: 768px) {
    width: 100%;
    justify-content: flex-start;
  }
`;

const MobileMenuButton = styled.button`
  display: none;
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #64748b;
  cursor: pointer;
  padding: 0.5rem;

  @media (max-width: 768px) {
    display: block;
  }
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background: ${props => props.online ? '#dcfce7' : '#fef2f2'};
  color: ${props => props.online ? '#166534' : '#dc2626'};
  font-size: 0.875rem;
  font-weight: 500;

  .indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: ${props => props.online ? '#22c55e' : '#ef4444'};
  }

  @media (max-width: 768px) {
    display: none;
  }
`;

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: FiHome },
    { path: '/scan', label: 'Scan Repository', icon: FiSearch },
    { path: '/history', label: 'Scan History', icon: FiList },
    { path: '/rules', label: 'Compliance Rules', icon: FiShield },
  ];

  const toggleMenu = () => setIsOpen(!isOpen);

  return (
    <NavbarContainer>
      <Logo as={Link} to="/">
        <FiShield className="icon" />
        Compliance Auditor
      </Logo>

      <NavLinks isOpen={isOpen}>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            isActive={location.pathname === item.path}
            onClick={() => setIsOpen(false)}
          >
            <item.icon className="icon" />
            {item.label}
          </NavLink>
        ))}
      </NavLinks>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <StatusIndicator online={true}>
          <div className="indicator" />
          <FiActivity style={{ fontSize: '1rem' }} />
          Online
        </StatusIndicator>

        <MobileMenuButton onClick={toggleMenu}>
          {isOpen ? <FiX /> : <FiMenu />}
        </MobileMenuButton>
      </div>
    </NavbarContainer>
  );
};

export default Navbar;
