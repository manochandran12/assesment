import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Textarea } from "./components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Badge } from "./components/ui/badge";
import { toast } from "sonner";
import { Toaster } from "./components/ui/sonner";
import { Copy, Link, Zap, Users, Settings } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [singleUrl, setSingleUrl] = useState("");
  const [customCode, setCustomCode] = useState("");
  const [bulkUrls, setBulkUrls] = useState("");
  const [shortenedUrls, setShortenedUrls] = useState([]);
  const [recentUrls, setRecentUrls] = useState([]);
  const [loading, setLoading] = useState(false);
  const [bulkLoading, setBulkLoading] = useState(false);

  useEffect(() => {
    fetchRecentUrls();
  }, []);

  const fetchRecentUrls = async () => {
    try {
      const response = await axios.get(`${API}/urls?limit=10`);
      setRecentUrls(response.data);
    } catch (error) {
      console.error("Error fetching recent URLs:", error);
    }
  };

  const handleSingleShorten = async (e) => {
    e.preventDefault();
    if (!singleUrl.trim()) {
      toast.error("Please enter a URL to shorten");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/shorten`, {
        url: singleUrl.trim(),
        custom_code: customCode.trim() || null
      });

      setShortenedUrls([response.data, ...shortenedUrls]);
      setSingleUrl("");
      setCustomCode("");
      toast.success("URL shortened successfully!");
      fetchRecentUrls();
    } catch (error) {
      const errorMessage = error.response?.data?.detail || "Failed to shorten URL";
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkShorten = async (e) => {
    e.preventDefault();
    if (!bulkUrls.trim()) {
      toast.error("Please enter URLs to shorten");
      return;
    }

    const urls = bulkUrls.split('\n').filter(url => url.trim());
    if (urls.length === 0) {
      toast.error("Please enter valid URLs");
      return;
    }

    setBulkLoading(true);
    try {
      const response = await axios.post(`${API}/shorten-bulk`, {
        urls: urls
      });

      setShortenedUrls([...response.data.results, ...shortenedUrls]);
      setBulkUrls("");
      
      const successCount = response.data.total_processed;
      const errorCount = response.data.errors.length;
      
      if (errorCount > 0) {
        toast.warning(`${successCount} URLs shortened successfully, ${errorCount} failed`);
        response.data.errors.forEach(error => {
          toast.error(error);
        });
      } else {
        toast.success(`All ${successCount} URLs shortened successfully!`);
      }
      
      fetchRecentUrls();
    } catch (error) {
      const errorMessage = error.response?.data?.detail || "Failed to shorten URLs";
      toast.error(errorMessage);
    } finally {
      setBulkLoading(false);
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success("Copied to clipboard!");
    } catch (error) {
      toast.error("Failed to copy to clipboard");
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center">
                <Link className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-800">QuickLink</h1>
                <p className="text-sm text-slate-500">Professional URL Shortener</p>
              </div>
            </div>
            <Badge variant="secondary" className="bg-green-100 text-green-700 border-green-200">
              <Zap className="w-3 h-3 mr-1" />
              Live
            </Badge>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        <div className="max-w-4xl mx-auto">
          
          {/* Hero Section */}
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold text-slate-800 mb-4">
              Shorten URLs with <span className="text-blue-600">Precision</span>
            </h2>
            <p className="text-lg text-slate-600 max-w-2xl mx-auto">
              Transform long URLs into short, shareable links. Support for custom codes and bulk operations.
            </p>
          </div>

          {/* Main Interface */}
          <Tabs defaultValue="single" className="w-full mb-8">
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="single" className="flex items-center gap-2">
                <Link className="w-4 h-4" />
                Single URL
              </TabsTrigger>
              <TabsTrigger value="bulk" className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                Bulk URLs
              </TabsTrigger>
            </TabsList>

            {/* Single URL Tab */}
            <TabsContent value="single">
              <Card className="border-0 shadow-lg bg-white/70 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Link className="w-5 h-5 text-blue-600" />
                    Shorten Single URL
                  </CardTitle>
                  <CardDescription>
                    Enter a URL and optionally customize the short code
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSingleShorten} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        Enter URL to shorten
                      </label>
                      <Input
                        type="text"
                        placeholder="https://example.com/very-long-url"
                        value={singleUrl}
                        onChange={(e) => setSingleUrl(e.target.value)}
                        className="w-full h-12 text-base"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        Custom short code <span className="text-slate-400">(optional)</span>
                      </label>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm text-slate-500 whitespace-nowrap">
                          {BACKEND_URL}/api/r/
                        </span>
                        <Input
                          type="text"
                          placeholder="my-custom-code"
                          value={customCode}
                          onChange={(e) => setCustomCode(e.target.value)}
                          className="flex-1 h-12"
                        />
                      </div>
                      <p className="text-xs text-slate-500 mt-1">
                        3-20 characters, letters, numbers, hyphens, and underscores only
                      </p>
                    </div>

                    <Button 
                      type="submit" 
                      disabled={loading}
                      className="w-full h-12 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-medium"
                    >
                      {loading ? "Shortening..." : "Shorten URL"}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Bulk URLs Tab */}
            <TabsContent value="bulk">
              <Card className="border-0 shadow-lg bg-white/70 backdrop-blur-sm">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-blue-600" />
                    Bulk URL Shortening
                  </CardTitle>
                  <CardDescription>
                    Enter multiple URLs (one per line) to shorten them all at once
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleBulkShorten} className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-slate-700 mb-2">
                        Enter URLs (one per line, max 50)
                      </label>
                      <Textarea
                        placeholder={`https://example.com/url1
https://example.com/url2
https://example.com/url3`}
                        value={bulkUrls}
                        onChange={(e) => setBulkUrls(e.target.value)}
                        className="min-h-[120px] text-base"
                        rows={6}
                      />
                    </div>

                    <Button 
                      type="submit" 
                      disabled={bulkLoading}
                      className="w-full h-12 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-medium"
                    >
                      {bulkLoading ? "Processing..." : "Shorten All URLs"}
                    </Button>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Results Section */}
          {shortenedUrls.length > 0 && (
            <Card className="border-0 shadow-lg bg-white/70 backdrop-blur-sm mb-8">
              <CardHeader>
                <CardTitle>Your Shortened URLs</CardTitle>
                <CardDescription>
                  Click to copy the shortened URL to your clipboard
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {shortenedUrls.map((url, index) => (
                  <div 
                    key={index}
                    className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200 hover:bg-slate-100 transition-colors"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-mono text-blue-600 font-medium truncate">
                          {url.short_url}
                        </p>
                        {url.custom && (
                          <Badge variant="secondary" className="bg-purple-100 text-purple-700 border-purple-200">
                            <Settings className="w-3 h-3 mr-1" />
                            Custom
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-slate-500 truncate" title={url.original_url}>
                        {url.original_url}
                      </p>
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(url.short_url)}
                      className="ml-3 flex-shrink-0"
                    >
                      <Copy className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Recent URLs Section */}
          {recentUrls.length > 0 && (
            <Card className="border-0 shadow-lg bg-white/70 backdrop-blur-sm">
              <CardHeader>
                <CardTitle>Recent URLs</CardTitle>
                <CardDescription>
                  Latest shortened URLs from all users
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {recentUrls.map((url, index) => (
                  <div 
                    key={index}
                    className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-mono text-blue-600 text-sm truncate">
                          {url.short_url}
                        </p>
                        {url.custom && (
                          <Badge variant="secondary" className="bg-purple-100 text-purple-700 border-purple-200">
                            Custom
                          </Badge>
                        )}
                        <Badge variant="outline" className="text-xs">
                          {url.click_count} clicks
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500 truncate" title={url.original_url}>
                        {url.original_url}
                      </p>
                      <p className="text-xs text-slate-400 mt-1">
                        {formatDate(url.created_at)}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(url.short_url)}
                      className="ml-3 flex-shrink-0"
                    >
                      <Copy className="w-3 h-3" />
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white/80 backdrop-blur-sm border-t border-slate-200 mt-16">
        <div className="container mx-auto px-6 py-8">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-3 mb-4">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                <Link className="w-5 h-5 text-white" />
              </div>
              <h3 className="text-lg font-semibold text-slate-800">QuickLink</h3>
            </div>
            <p className="text-slate-600 text-sm">
              Professional URL shortening service with custom codes and bulk operations
            </p>
            <p className="text-slate-400 text-xs mt-2">
              Built with FastAPI, React, and MongoDB
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;