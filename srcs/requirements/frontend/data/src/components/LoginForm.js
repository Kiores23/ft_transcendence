import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, Form } from 'react-bootstrap'; // Importation de React-Bootstrap
import { useUser } from '../contexts/UserContext.js';

const LoginForm = ({ onLogin }) => {
  /*const [credentials, setCredentials] = useState({
    username: '',
    password: '',
    totpToken: '',
  });*/
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  })
  const [showModal, setShowModal] = useState(false);
  const [step, setStep] = useState('credentials'); // 'credentials' or 'totp'
  const { login42 } = useUser();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prevData => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin(formData);
    /*try {
      const has_2fa = onLogin(credentials);
      if (has_2fa) {
        setStep('totp');
      } else {
        console.log('Login successful');
      }
    } catch (error) {
      console.error('Login failed:', error);
    }*/
  };

  return (
    <div>
      <h1 className="title">LOGIN</h1>
      <div className="BorderBox">
        <Form onSubmit={handleSubmit}> {/* Utilisation du composant Form de React-Bootstrap */}
          <Form.Group controlId="formBasicUsername"> {/* Form.Group est utilisé pour un contrôle de champ */}
            <Form.Label>Username</Form.Label>
            <Form.Control
              type="text"
              placeholder="Enter your username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
            />
          </Form.Group>

          <Form.Group controlId="formBasicPassword">
            <Form.Label>Password</Form.Label>
            <Form.Control
              type="password"
              placeholder="Enter your password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
            />
          </Form.Group>

          <Button className="options" variant="primary" type="submit">LOG IN</Button> {/* Utilisation du bouton de React-Bootstrap */}
          
          {/* Autre bouton pour "Log In with 42", variant "secondary" pour l'option secondaire */}
          <Button className="options" variant="secondary" onClick={login42}>LOG IN WITH 42</Button>

          <div className="mt-3">
            <Link to="/register">Don't have an account? Register</Link>
            <br/>
            <Link to='/forgot-password'>Forgot Password ?</Link>
          </div>
        </Form>
      </div>
    </div>
  );
}

export default LoginForm;
