const compareButton = document.getElementById("compareButton");
const loading = document.getElementById("loading");
const comparisonSection = document.getElementById("comparisonSection");
const advisorSection = document.getElementById("advisorSection");
const sendButton = document.getElementById("sendButton");
const questionInput = document.getElementById("questionInput");
const chatMessages = document.getElementById("chatMessages");
const summary = document.getElementById("summary");
const hotelCards = document.getElementById("hotelCards");
const comparisonModal = document.getElementById("comparisonModal");
const closeComparisonModalButton = document.getElementById("closeComparisonModal");
const cancelComparisonButton = document.getElementById("cancelComparisonButton");
const confirmComparisonButton = document.getElementById("confirmComparisonButton");
const travellerSummary = document.getElementById("travellerSummary");
const childrenInput = document.getElementById("childrenInput");
const childAgesContainer = document.getElementById("childAgesContainer");
let advisorHistory = [];
let hotelMap = new Map();
let selectedHotels = [];
let recommendedHotel = null;
let comparisonSessionId = null;

function renderChildAgeInputs() {
    const children = Number(childrenInput.value || 0);
    const existingValues = Array.from(
        childAgesContainer.querySelectorAll("input")
    ).map(input => input.value);

    childAgesContainer.innerHTML = "";

    for (let index = 0; index < children; index += 1) {
        const wrapper = document.createElement("div");
        wrapper.className = "child-age-field";

        wrapper.innerHTML = `
            <label for="childAge${index}">Child ${index + 1} age</label>
            <input
                id="childAge${index}"
                class="child-age-input"
                type="number"
                min="0"
                max="17"
                value="${existingValues[index] ?? ""}"
                placeholder="Age"
            >
        `;

        childAgesContainer.appendChild(wrapper);
    }
}

function getChildAges() {
    const children = Number(childrenInput.value || 0);

    if (children === 0) {
        return [];
    }

    const inputs = Array.from(
        childAgesContainer.querySelectorAll(".child-age-input")
    );

    if (inputs.length !== children || inputs.some(input => input.value === "")) {
        return null;
    }

    return inputs.map(input => Number(input.value));
}

childrenInput.addEventListener("input", renderChildAgeInputs);
renderChildAgeInputs();

function connectToHotelStream(searchId) {
    const eventSource = new EventSource(
        `/rateloc/search/${searchId}/stream`
    );

    console.log("Connected to stream:", searchId);

    eventSource.addEventListener("supplier_batch", function (event) {
        const data = JSON.parse(event.data);
        console.log("Supplier batch received:", data);
    });

    eventSource.addEventListener("search_complete", function (event) {
        const data = JSON.parse(event.data);

        console.log("Search complete:", data);

        if (data.hotels) {
            for (const hotel of data.hotels) {
                hotelMap.set(hotel.uniqueCode, hotel);
            }
        }

        renderHotels();
        eventSource.close();
    });

    eventSource.onerror = function (error) {
        console.error("Hotel stream error:", error);
    };
}

function selectHotel(uniqueCode) {
    const hotel = hotelMap.get(uniqueCode);

    if (!hotel) {
        return;
    }

    const existingIndex = selectedHotels.findIndex(
        item => item.uniqueCode === uniqueCode
    );

    if (existingIndex !== -1) {
        selectedHotels.splice(existingIndex, 1);
    } else {
        if (selectedHotels.length >= 3) {
            alert("You can compare up to 3 hotels.");
            return;
        }

        selectedHotels.push(hotel);
    }

    document.getElementById("selectedCount").textContent =
        `Selected: ${selectedHotels.length} / 3`;

    console.log("Selected hotels:", selectedHotels);

    renderHotels();
}

function renderHotels() {
    const hotelResults = document.getElementById("hotelResults");

    hotelResults.innerHTML = "";

    for (const hotel of hotelMap.values()) {
        const card = document.createElement("div");

        card.className = "hotel-card";

        const isSelected = selectedHotels.some(
            item => item.uniqueCode === hotel.uniqueCode
        );

        card.innerHTML = `
            <img
                src="${hotel.image || ""}"
                alt="${hotel.title || "Hotel"}"
                class="hotel-image"
            >

            <h3>${hotel.title || ""}</h3>
            <p>${hotel.address || ""}</p>
            <p>${hotel.rating || ""} Star</p>
            <p>${hotel.roomName || ""}</p>
            <p>${hotel.boardBase || ""}</p>

            <strong>
                ${hotel.price?.currency || ""}
                ${hotel.price?.totalPrice || ""}
            </strong>

            <p>
                ${hotel.refundable ? "Refundable" : "Non-refundable"}
            </p>

            <button
                onclick="selectHotel('${hotel.uniqueCode}')"
                class="${isSelected ? "selected-hotel-button" : ""}"
            >
                ${isSelected ? "Selected ✓" : "Select"}
            </button>
        `;

        hotelResults.appendChild(card);
    }
}

async function searchHotels() {
    hotelMap.clear();
    selectedHotels = [];
    advisorHistory = [];
    recommendedHotel = null;
    chatMessages.innerHTML = "";

    document.getElementById("selectedCount").textContent =
        "Selected: 0 / 3";

    const destination =
        document.getElementById("destinationInput").value.trim();
    const checkInDate =
        document.getElementById("checkInInput").value;
    const checkOutDate =
        document.getElementById("checkOutInput").value;
    const adults =
        Number(document.getElementById("adultsInput").value);
    const children =
        Number(document.getElementById("childrenInput").value);
    const nationality =
        document.getElementById("nationalityInput").value.trim();
    const childAges = getChildAges();

    if (!destination) {
        alert("Please enter a destination.");
        return;
    }

    if (!checkInDate || !checkOutDate) {
        alert("Please select check-in and check-out dates.");
        return;
    }

    if (children > 0 && childAges === null) {
        alert("Please enter the age of each child.");
        return;
    }

    const payload = {
        checkInDate: checkInDate,
        checkOutDate: checkOutDate,
        currency: "INR",
        location: destination,
        nationality: nationality,
        residency: nationality,
        page: {
            page: 1,
            size: 20
        },
        rooms: [
            {
                adults: adults,
                children: children,
                childAges: childAges
            }
        ],
        sort: "RANKING"
    };

    console.log("Searching RateLoc with:", payload);

    const response = await fetch("/rateloc/search", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        throw new Error(`Hotel search failed: ${response.status}`);
    }

    const result = await response.json();
    console.log("Search created:", result);

    const searchId = result.data.searchId;
    connectToHotelStream(searchId);
}

sendButton.addEventListener("click", sendAdvisorQuestion);

questionInput.addEventListener("keydown", function (event) {
    if (event.key === "Enter") {
        sendAdvisorQuestion();
    }
});

async function sendAdvisorQuestion() {
    const question = questionInput.value.trim();

    if (!question) {
        return;
    }

    const childAges = getChildAges();
    const historyForRequest = [...advisorHistory];

    addChatMessage("user", question);
    questionInput.value = "";
    sendButton.disabled = true;

    try {
        const advisorRequest = {
            destination: document.getElementById("destinationInput").value.trim(),
            adults: Number(document.getElementById("adultsInput").value),
            children: Number(document.getElementById("childrenInput").value),
            child_ages: childAges ?? [],
            history: historyForRequest,
            recommended_hotel: recommendedHotel,
            session_id: comparisonSessionId,
            question: question,
            hotels: selectedHotels.map(hotel => ({
                hotel_code: hotel.uniqueCode,
                hotel_name: hotel.title,
                address: hotel.address ?? null,
                rating: hotel.rating ? Number(hotel.rating) : null,
                latitude: hotel.latitude ?? null,
                longitude: hotel.longitude ?? null,
                price: hotel.price?.totalPrice ?? null,
                currency: hotel.price?.currency ?? null,
                room_name: hotel.roomName ?? null,
                board_basis: hotel.boardBase ?? null,
                refundable: hotel.refundable ?? null,
                deadline: hotel.deadline ?? null,
                amenities: hotel.amenities ?? [],
                web_evidence: []
            }))
        };

        console.log("Advisor request:", advisorRequest);

        const response = await fetch("/advisor", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(advisorRequest)
        });

        if (!response.ok) {
            throw new Error(`Advisor request failed: ${response.status}`);
        }

        const data = await response.json();

        advisorHistory.push(
            { role: "user", content: question },
            { role: "assistant", content: data.answer }
        );

        addChatMessage("assistant", data.answer);

    } catch (error) {
        console.error(error);

        addChatMessage(
            "assistant",
            "Sorry, the Hotel Advisor is temporarily unavailable."
        );

    } finally {
        sendButton.disabled = false;
        questionInput.focus();
    }
}

function addChatMessage(role, text) {
    const message = document.createElement("div");

    message.className =
        role === "user"
            ? "chat-message user-message"
            : "chat-message assistant-message";

    message.textContent = text;

    chatMessages.appendChild(message);

    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function openComparisonModal() {
    if (selectedHotels.length < 2) {
        alert("Please select at least 2 hotels.");
        return;
    }

    const adults = Number(document.getElementById("adultsInput").value);
    const children = Number(document.getElementById("childrenInput").value);
    const childAges = getChildAges();

    if (children > 0 && childAges === null) {
        alert("Please enter the age of each child before comparing.");
        return;
    }

    const childText = children > 0
        ? `, ${children} child${children === 1 ? "" : "ren"}${childAges.length ? ` (age${childAges.length > 1 ? "s" : ""} ${childAges.join(", ")})` : ""}`
        : "";

    travellerSummary.textContent =
        `${adults} adult${adults === 1 ? "" : "s"}${childText} · ${selectedHotels.length} hotels selected`;

    comparisonModal.classList.remove("hidden");
}

function closeComparisonModal() {
    comparisonModal.classList.add("hidden");
}

function getComparisonPreferences() {
    const priorities = Array.from(
        document.querySelectorAll('input[name="comparisonPriority"]:checked')
    ).map(input => input.value);

    const customRequirement =
        document.getElementById("customRequirement").value.trim();

    return {
        priorities: priorities,
        custom_requirement: customRequirement || null,
        price_preference: document.getElementById("pricePreference").value
    };
}

async function runComparison() {
    const childAges = getChildAges();

    const comparisonRequest = {
        destination: document.getElementById("destinationInput").value.trim(),
        adults: Number(document.getElementById("adultsInput").value),
        children: Number(document.getElementById("childrenInput").value),
        child_ages: childAges ?? [],
        comparison_preferences: getComparisonPreferences(),
        hotels: selectedHotels
    };

    closeComparisonModal();
    loading.classList.remove("hidden");
    comparisonSection.classList.add("hidden");
    advisorSection.classList.add("hidden");
    compareButton.disabled = true;
    confirmComparisonButton.disabled = true;

    try {
        console.log("Comparison request:", comparisonRequest);

        const response = await fetch("/compare/rateloc", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(comparisonRequest)
        });

        if (!response.ok) {
            throw new Error(`Comparison failed: ${response.status}`);
        }

        const data = await response.json();
        comparisonSessionId = data.session_id ?? null;
        console.log("AI comparison:", data);

        recommendedHotel = data.recommended_hotel ?? null;

        console.log(
            "Recommended hotel stored:",
            recommendedHotel
        );

        advisorHistory = [];
        chatMessages.innerHTML = "";
        renderComparison(data);

        comparisonSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    } catch (error) {
        console.error(error);
        summary.textContent = "Unable to generate the hotel comparison.";
        comparisonSection.classList.remove("hidden");

    } finally {
        loading.classList.add("hidden");
        compareButton.disabled = false;
        confirmComparisonButton.disabled = false;
    }
}

compareButton.addEventListener("click", openComparisonModal);
confirmComparisonButton.addEventListener("click", runComparison);
cancelComparisonButton.addEventListener("click", closeComparisonModal);
closeComparisonModalButton.addEventListener("click", closeComparisonModal);
comparisonModal.addEventListener("click", function (event) {
    if (event.target === comparisonModal) {
        closeComparisonModal();
    }
});

function renderComparison(data) {
    summary.innerHTML = `
        <div class="recommendation">
            <strong>Recommended:</strong>
            ${data.recommended_hotel ?? "No AI recommendation available"}

            <p>${data.summary ?? ""}</p>

            <p>
                <strong>Cheapest:</strong>
                ${data.cheapest_hotel ?? "Unknown"}
            </p>

            ${
                data.price_difference !== null
                    ? `
                        <p>
                            <strong>Price difference:</strong>
                            ${formatPrice(data.price_difference)}
                        </p>
                    `
                    : ""
            }
        </div>
    `;

    hotelCards.innerHTML = "";

    data.hotels.forEach(hotel => {
        const card = document.createElement("div");

        card.className = "hotel-card";

        const pros = hotel.pros
            .map(pro => `<li>${escapeHtml(pro)}</li>`)
            .join("");

        const cons = hotel.cons
            .map(con => `<li>${escapeHtml(con)}</li>`)
            .join("");

        card.innerHTML = `
            <h3>${escapeHtml(hotel.hotel_name)}</h3>

            <div class="hotel-price">
                ${formatPrice(hotel.price, hotel.currency)}
            </div>

            ${
                pros.length
                    ? `
                        <h4>Pros</h4>
                        <ul>${pros}</ul>
                    `
                    : ""
            }

            ${
                cons.length
                    ? `
                        <h4>Things to consider</h4>
                        <ul>${cons}</ul>
                    `
                    : ""
            }

            ${
                hotel.recommendation_reason
                    ? `
                        <p class="reason">
                            ${escapeHtml(hotel.recommendation_reason)}
                        </p>
                    `
                    : ""
            }
        `;

        hotelCards.appendChild(card);
    });

    comparisonSection.classList.remove("hidden");
    advisorSection.classList.remove("hidden");
}

function formatPrice(value, currency = "INR") {
    if (value === null || value === undefined) {
        return "Price unavailable";
    }

    try {
        return new Intl.NumberFormat("en-IN", {
            style: "currency",
            currency: currency
        }).format(value);

    } catch {
        return `${value} ${currency}`;
    }
}

function escapeHtml(value) {
    if (!value) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
