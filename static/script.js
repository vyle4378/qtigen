const textareas = document.querySelectorAll("textarea");
const userInput = document.getElementById("userInput");
const generateButton = document.getElementById("generateButton");
const responseArea = document.getElementById("responseArea");
const convertButton = document.getElementById("convertButton");
const formatButton = document.getElementById("formatButton");

userInput.addEventListener("input", () => {
  userInput.style.height = "auto";
  userInput.style.height = userInput.scrollHeight - 20 + "px";
});

async function generateProblems(userInput) {
  const message = userInput.value;
  const response = await fetch("/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  const data = await response.json();
  responseArea.value = data.problems;
  console.log("done generating problems");
}

async function formatProblems(responseArea) {
  const problems = responseArea.value;
  const response = await fetch("/format", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ problems }),
  });

  const data = await response.json();
  responseArea.value = data.problems;
  console.log("done formatting problems");
}

async function convertProblems() {
  const problems = responseArea.value;
  const zipName = document.getElementById("zipName").value;

  const response = await fetch("/convert", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ problems }),
  });

  if (!response.ok) {
    const error = await response.json();
    alert(error.detail || "Conversion failed");
    return;
  }
  const zip = await response.blob();
  const url = URL.createObjectURL(zip);
  const a = document.createElement("a");
  a.href = url;
  a.download = zipName + ".zip";
  a.click();
  a.remove(); // Removes the hidden "a" element from the html
  URL.revokeObjectURL(url); // Frees up memory used by the blob URL
}

generateButton.addEventListener("click", () => {
  if (userInput.value !== "") {
    generateProblems(userInput);
  } else {
    alert("Please enter a topic for problem generation");
  }
});

formatButton.addEventListener("click", () => {
  if (responseArea.value !== "") {
    formatProblems(responseArea);
  } else {
    alert("Please enter problems to format");
  }
});

convertButton.addEventListener("click", () => {
  if (responseArea.value !== "") {
    convertProblems();
  } else {
    alert("Please enter problems to convert");
  }
});
