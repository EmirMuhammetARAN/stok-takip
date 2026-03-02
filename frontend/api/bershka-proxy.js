export default async function handler(req, res) {
  const { url } = req.query;
  const response = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      'Accept': 'application/json',
    }
  });
  const data = await response.json();
  res.json(data);
}