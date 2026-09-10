const form =
    document.getElementById("analysisForm");

const fileInput =
    document.getElementById("image");

const dropZone =
    document.getElementById("dropZone");

const dropPlaceholder =
    document.getElementById("dropPlaceholder");

const previewContainer =
    document.getElementById("previewContainer");

const preview =
    document.getElementById("preview");

const fileName =
    document.getElementById("fileName");

const fileSize =
    document.getElementById("fileSize");

const removeImageButton =
    document.getElementById("removeImage");

const analyzeButton =
    document.getElementById("analyzeButton");

const loading =
    document.getElementById("loading");

const loadingText =
    document.getElementById("loadingText");

const resultSection =
    document.getElementById("result");

const errorBox =
    document.getElementById("error");

const newAnalysisButton =
    document.getElementById("newAnalysis");


let selectedFile = null;


/* =========================================================
   FILE SELECTION
========================================================= */

dropZone.addEventListener(
    "click",
    function(event) {

        if (
            event.target === removeImageButton
        ) {
            return;
        }

        fileInput.click();
    }
);


fileInput.addEventListener(
    "change",
    function() {

        if (fileInput.files.length > 0) {

            handleFile(
                fileInput.files[0]
            );
        }
    }
);


/* =========================================================
   DRAG AND DROP
========================================================= */

dropZone.addEventListener(
    "dragover",
    function(event) {

        event.preventDefault();

        dropZone.classList.add(
            "dragging"
        );
    }
);


dropZone.addEventListener(
    "dragleave",
    function() {

        dropZone.classList.remove(
            "dragging"
        );
    }
);


dropZone.addEventListener(
    "drop",
    function(event) {

        event.preventDefault();

        dropZone.classList.remove(
            "dragging"
        );

        if (
            event.dataTransfer.files.length
            > 0
        ) {

            handleFile(
                event.dataTransfer.files[0]
            );
        }
    }
);


/* =========================================================
   VALIDATE + PREVIEW
========================================================= */

function handleFile(file) {

    errorBox.textContent = "";

    const allowedTypes = [
        "image/jpeg",
        "image/png"
    ];


    if (
        !allowedTypes.includes(
            file.type
        )
    ) {

        showError(
            "Please select a JPG, JPEG or PNG image."
        );

        return;
    }


    const maxSize =
        10 * 1024 * 1024;


    if (
        file.size > maxSize
    ) {

        showError(
            "Image size must be below 10 MB."
        );

        return;
    }


    selectedFile = file;


    preview.src =
        URL.createObjectURL(
            file
        );


    fileName.textContent =
        file.name;


    fileSize.textContent =
        formatFileSize(
            file.size
        );


    dropPlaceholder.style.display =
        "none";


    previewContainer.style.display =
        "flex";
}


/* =========================================================
   REMOVE IMAGE
========================================================= */

removeImageButton.addEventListener(
    "click",
    function(event) {

        event.stopPropagation();

        resetImage();
    }
);


function resetImage() {

    selectedFile = null;

    fileInput.value = "";

    preview.src = "";

    previewContainer.style.display =
        "none";

    dropPlaceholder.style.display =
        "block";
}


/* =========================================================
   SUBMIT
========================================================= */

form.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();


        if (!selectedFile) {

            showError(
                "Please upload a kidney CT image."
            );

            return;
        }


        errorBox.textContent = "";

        resultSection.style.display =
            "none";

        loading.style.display =
            "flex";

        analyzeButton.disabled =
            true;


        const formData =
            new FormData();


        formData.append(
            "image",
            selectedFile
        );


        const question =
            document.getElementById(
                "question"
            ).value;


        formData.append(
            "question",
            question
        );


        startLoadingMessages();


        try {

            const response =
                await fetch(
                    "/analyze",
                    {
                        method: "POST",
                        body: formData
                    }
                );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.error ||
                    "Analysis failed."
                );
            }


            displayResults(
                data
            );

        }

        catch (error) {

            showError(
                error.message
            );

        }

        finally {

            stopLoadingMessages();

            loading.style.display =
                "none";

            analyzeButton.disabled =
                false;
        }

    }
);


/* =========================================================
   LOADING MESSAGE
========================================================= */

let loadingInterval = null;


function startLoadingMessages() {

    const messages = [

        "Running Swin Transformer classification...",

        "Calculating class probabilities...",

        "Retrieving relevant medical knowledge...",

        "Generating grounded clinical advisory..."

    ];


    let index = 0;


    loadingText.textContent =
        messages[index];


    loadingInterval =
        setInterval(
            function() {

                index =
                    (index + 1)
                    % messages.length;

                loadingText.textContent =
                    messages[index];

            },
            1700
        );
}


function stopLoadingMessages() {

    if (loadingInterval) {

        clearInterval(
            loadingInterval
        );

        loadingInterval = null;
    }
}


/* =========================================================
   DISPLAY RESULT
========================================================= */

function displayResults(data) {

    document.getElementById(
        "prediction"
    ).textContent =
        data.prediction;


    document.getElementById(
        "confidence"
    ).textContent =
        Number(
            data.confidence
        ).toFixed(2)
        + "%";


    document.getElementById(
        "confidenceFill"
    ).style.width =
        data.confidence
        + "%";


    displayProbabilities(
        data.probabilities
    );


    displayAdvisory(
        data.advisory
    );


    document.getElementById(
        "disclaimer"
    ).textContent =
        data.disclaimer;


    resultSection.style.display =
        "block";


    setTimeout(
        function() {

            resultSection.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        },
        100
    );
}


/* =========================================================
   PROBABILITY BARS
========================================================= */

function displayProbabilities(
    probabilities
) {

    const container =
        document.getElementById(
            "probabilities"
        );


    container.innerHTML = "";


    const sorted =
        Object.entries(
            probabilities
        ).sort(
            (a, b) =>
                b[1] - a[1]
        );


    sorted.forEach(
        function([
            className,
            probability
        ]) {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "probability-row";


            const header =
                document.createElement(
                    "div"
                );


            header.className =
                "probability-header";


            const name =
                document.createElement(
                    "strong"
                );


            name.textContent =
                className;


            const percentage =
                document.createElement(
                    "span"
                );


            percentage.textContent =
                Number(
                    probability
                ).toFixed(2)
                + "%";


            header.appendChild(
                name
            );


            header.appendChild(
                percentage
            );


            const bar =
                document.createElement(
                    "div"
                );


            bar.className =
                "probability-bar";


            const fill =
                document.createElement(
                    "div"
                );


            fill.className =
                "probability-fill";


            fill.style.width =
                "0%";


            bar.appendChild(
                fill
            );


            row.appendChild(
                header
            );


            row.appendChild(
                bar
            );


            container.appendChild(
                row
            );


            setTimeout(
                function() {

                    fill.style.width =
                        probability + "%";

                },
                100
            );
        }
    );
}


/* =========================================================
   SAFELY DISPLAY GEMINI RESPONSE
========================================================= */

function displayAdvisory(text) {

    const container =
        document.getElementById(
            "advisory"
        );


    container.innerHTML = "";


    const lines =
        String(text)
        .split("\n");


    let currentList = null;


    lines.forEach(
        function(line) {

            const trimmed =
                line.trim();


            if (!trimmed) {

                currentList = null;

                return;
            }


            if (
                trimmed.startsWith(
                    "### "
                )
            ) {

                currentList = null;

                const heading =
                    document.createElement(
                        "h3"
                    );


                heading.textContent =
                    trimmed.substring(4);


                container.appendChild(
                    heading
                );


                return;
            }


            if (
                trimmed.startsWith(
                    "* "
                )
                ||
                trimmed.startsWith(
                    "- "
                )
            ) {

                if (!currentList) {

                    currentList =
                        document.createElement(
                            "ul"
                        );


                    container.appendChild(
                        currentList
                    );
                }


                const item =
                    document.createElement(
                        "li"
                    );


                item.textContent =
                    trimmed.substring(2)
                    .replace(
                        /\*\*/g,
                        ""
                    );


                currentList.appendChild(
                    item
                );


                return;
            }


            currentList = null;


            const paragraph =
                document.createElement(
                    "p"
                );


            paragraph.textContent =
                trimmed.replace(
                    /\*\*/g,
                    ""
                );


            container.appendChild(
                paragraph
            );
        }
    );
}


/* =========================================================
   HELPERS
========================================================= */

function formatFileSize(bytes) {

    if (
        bytes < 1024 * 1024
    ) {

        return (
            (
                bytes / 1024
            ).toFixed(1)
            + " KB"
        );
    }


    return (
        (
            bytes /
            (1024 * 1024)
        ).toFixed(2)
        + " MB"
    );
}


function showError(message) {

    errorBox.textContent =
        message;


    errorBox.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });
}


/* =========================================================
   NEW ANALYSIS
========================================================= */

newAnalysisButton.addEventListener(
    "click",
    function() {

        resetImage();


        document.getElementById(
            "question"
        ).value = "";


        resultSection.style.display =
            "none";


        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });
    }
);