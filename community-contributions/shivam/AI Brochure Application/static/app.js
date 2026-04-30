document
  .getElementById("brochureForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();

    const companyName = document.getElementById("companyName").value;
    const companyUrl = document.getElementById("companyUrl").value;
    const loader = document.getElementById("loader");
    const resultDiv = document.getElementById("result");
    const btn = document.getElementById("submitBtn");
    const markdownOutput = document.getElementById("markdownOutput");

    // UI Updates
    loader.classList.remove("hidden");
    resultDiv.classList.add("hidden");
    btn.disabled = true;
    markdownOutput.innerHTML = ""; // Clear previous output

    try {
      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_name: companyName, url: companyUrl }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to generate");
      }

      // Hide loader once we start receiving the stream
      loader.classList.add("hidden");
      resultDiv.classList.remove("hidden");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullMarkdown = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        fullMarkdown += chunk;
        
        // Convert the accumulating Markdown into HTML
        markdownOutput.innerHTML = marked.parse(fullMarkdown);
        
        // Scroll to bottom as it generates
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
      }

    } catch (error) {
      alert("Error: " + error.message);
      loader.classList.add("hidden");
    } finally {
      btn.disabled = false;
    }
  });
