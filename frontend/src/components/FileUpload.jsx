import React, { useState } from 'react';
import { Box, Button, Typography, LinearProgress } from '@mui/material';
import { uploadFile } from '../api';

function FileUpload({ token, onUpload }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [fileInfo, setFileInfo] = useState(null);

  const handleChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setError('');
    try {
      const info = await uploadFile(file, token);
      setFileInfo(info);
      if (onUpload) onUpload(info);
    } catch (err) {
      setError('Upload failed');
    }
    setUploading(false);
  };

  return (
    <Box mt={2}>
      <Button variant="outlined" component="label" disabled={uploading}>
        Upload File
        <input type="file" hidden onChange={handleChange} />
      </Button>
      {uploading && <LinearProgress sx={{ mt: 1 }} />}
      {fileInfo && <Typography variant="body2" mt={1}>Uploaded: {fileInfo.filename} ({fileInfo.size} bytes)</Typography>}
      {error && <Typography color="error" variant="body2">{error}</Typography>}
    </Box>
  );
}

export default FileUpload;
