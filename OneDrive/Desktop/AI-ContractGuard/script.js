const API_URL = "http://127.0.0.1:5000/analyze";


/* PDF.js worker */

pdfjsLib.GlobalWorkerOptions.workerSrc =
    "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";


/* File inputs */

const contractFile = document.getElementById("contractFile");
const policyFile = document.getElementById("policyFile");
const regulationFile = document.getElementById("regulationFile");

const contractName = document.getElementById("contractName");
const policyName = document.getElementById("policyName");
const regulationName = document.getElementById("regulationName");


contractFile.addEventListener("change", () => {
    showFileName(contractFile, contractName);
});

policyFile.addEventListener("change", () => {
    showFileName(policyFile, policyName);
});

regulationFile.addEventListener("change", () => {
    showFileName(regulationFile, regulationName);
});


function showFileName(input, element) {

    if (input.files.length > 0) {
        element.textContent = input.files[0].name;
    } else {
        element.textContent = "No file selected";
    }
}


/* Read PDF */

async function extractPDFText(file) {

    const arrayBuffer = await file.arrayBuffer();

    const pdf = await pdfjsLib.getDocument({
        data: arrayBuffer
    }).promise;

    let fullText = "";

    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber++) {

        const page = await pdf.getPage(pageNumber);

        const content = await page.getTextContent();

        const pageText = content.items
            .map(item => item.str)
            .join(" ");

        fullText += pageText + "\n";
    }

    return fullText;
}


/* Analyze */

document.getElementById("analyzeBtn").addEventListener("click", async () => {

    const errorBox = document.getElementById("errorMessage");
    const loading = document.getElementById("loading");

    errorBox.classList.add("hidden");

    if (
        !contractFile.files.length ||
        !policyFile.files.length ||
        !regulationFile.files.length
    ) {

        errorBox.textContent =
            "Please upload Contract, Company Policy and Regulation PDFs.";

        errorBox.classList.remove("hidden");

        return;
    }


    loading.classList.remove("hidden");


    try {

        /* Extract document text */

        const contractText =
            await extractPDFText(contractFile.files[0]);

        const policyText =
            await extractPDFText(policyFile.files[0]);

        const regulationText =
            await extractPDFText(regulationFile.files[0]);


        /* Send to backend */

        const response = await fetch(API_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                contract: contractText,
                policy: policyText,
                regulation: regulationText

            })

        });


        if (!response.ok) {
            throw new Error("Backend analysis failed.");
        }


        const result = await response.json();


        updateDashboard(result);

        updateAnalysis(result);

        updateVerification(result);

        addAuditEntry(result);


    } catch (error) {

        console.error(error);

        errorBox.textContent =
            "Unable to analyze documents. Make sure the Flask backend is running.";

        errorBox.classList.remove("hidden");

    } finally {

        loading.classList.add("hidden");

    }

});


/* Dashboard */

function updateDashboard(result) {

    document.getElementById("documentCount").textContent = "3";

    document.getElementById("conflictCount").textContent =
        result.conflicts.length;

    document.getElementById("riskScore").textContent =
        result.risk_score;

    document.getElementById("riskStatus").textContent =
        result.severity;
}


/* Analysis */

function updateAnalysis(result) {

    document.getElementById("riskNumber").textContent =
        result.risk_score;

    document.getElementById("riskTitle").textContent =
        result.severity + " RISK";

    document.getElementById("riskDescription").textContent =
        result.risk_description;


    if (result.conflicts.length > 0) {

        document.getElementById("conflictTitle").textContent =
            result.conflicts[0].type;

        document.getElementById("conflictDescription").textContent =
            result.conflicts[0].description;

    } else {

        document.getElementById("conflictTitle").textContent =
            "No Conflict Detected";

        document.getElementById("conflictDescription").textContent =
            "The analyzed requirements are aligned.";

    }


    /* Actions */

    const actionList =
        document.getElementById("actionList");

    actionList.innerHTML = "";

    result.recommended_actions.forEach(action => {

        const li = document.createElement("li");

        li.textContent = action;

        actionList.appendChild(li);

    });


    /* Evidence */

    const evidenceList =
        document.getElementById("evidenceList");

    evidenceList.innerHTML = "";

    result.evidence.forEach(item => {

        const li = document.createElement("li");

        li.textContent = item;

        evidenceList.appendChild(li);

    });

}


/* Official Source Verification */

function updateVerification(result) {

    const status =
        document.getElementById("verificationStatus");

    const message =
        document.getElementById("verificationMessage");

    const source =
        document.getElementById("verificationSource");

    const documentStatus =
        document.getElementById("documentStatus");

    const lastChecked =
        document.getElementById("lastChecked");

    const note =
        document.getElementById("verificationNote");


    /*
       IMPORTANT:
       We do NOT automatically show "Government Verified".
       Backend must explicitly return verification_status.
    */


    status.textContent =
        result.verification.status;

    message.textContent =
        result.verification.message;

    source.textContent =
        result.verification.source;

    documentStatus.textContent =
        result.verification.document_status;

    lastChecked.textContent =
        result.verification.last_checked;

    note.textContent =
        result.verification.note;
}


/* Audit */

function addAuditEntry(result) {

    const auditCard =
        document.querySelector(".audit-card");

    const item =
        document.createElement("div");

    item.className = "audit-item";


    const now =
        new Date().toLocaleTimeString();


    item.innerHTML = `
        <span class="audit-dot"></span>

        <div>
            <strong>Compliance Analysis Completed</strong>
            <p>
                Risk ${result.risk_score}/100 —
                ${result.severity}
            </p>
        </div>

        <time>${now}</time>
    `;


    auditCard.appendChild(item);
}