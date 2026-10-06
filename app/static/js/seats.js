/**
 * CineBook Interactive Seat Selection & Real-Time Locking
 * Dynamically fetches seat availability from MySQL via Flask API.
 * Enforces seat selection rules and manages temporary 5-minute reservation countdown.
 */

document.addEventListener("DOMContentLoaded", function () {
    const seatGrid = document.getElementById("seat-grid");
    if (!seatGrid) return;

    const showId = seatGrid.dataset.showId;
    const ticketPrice = parseFloat(seatGrid.dataset.ticketPrice || 0);

    const selectedSeatsText = document.getElementById("selected-seats-text");
    const totalPriceText = document.getElementById("total-price-text");
    const proceedBtn = document.getElementById("proceed-btn");
    const timerBar = document.getElementById("lock-timer-bar");
    const timerDisplay = document.getElementById("timer-display");
    const messageBox = document.getElementById("message-box");

    let selectedSeats = new Map(); // seatId -> { id, label, type }
    let countdownInterval = null;

    function showMessage(msg, type = "danger") {
        if (!messageBox) return;
        messageBox.innerHTML = `
            <div class="alert alert-${type}">
                <span>${msg}</span>
                <button type="button" class="btn" style="padding:0; background:none; color:inherit; font-size:1.1rem;" onclick="this.parentElement.remove()">✕</button>
            </div>
        `;
    }

    // 1. Fetch live seat map from database
    async function loadSeats() {
        try {
            const res = await fetch(`/api/show/${showId}/seats`);
            const data = await res.json();

            if (!data.success) {
                showMessage(data.error || "Failed to load seats from database.");
                return;
            }

            renderGrid(data.seats);
        } catch (err) {
            console.error("Error fetching seat map:", err);
            showMessage("Network error loading seat layout. Please refresh.");
        }
    }

    // 2. Render seat rows and columns
    function renderGrid(seats) {
        seatGrid.innerHTML = "";

        // Group seats by row_label
        const rows = {};
        seats.forEach(seat => {
            if (!rows[seat.row_label]) {
                rows[seat.row_label] = [];
            }
            rows[seat.row_label].push(seat);
        });

        const sortedRowLabels = Object.keys(rows).sort();

        sortedRowLabels.forEach(rowLabel => {
            const rowElem = document.createElement("div");
            rowElem.className = "seat-row";

            // Row letter header
            const letterLabel = document.createElement("div");
            letterLabel.className = "row-letter";
            letterLabel.textContent = rowLabel;
            rowElem.appendChild(letterLabel);

            // Container for seat buttons
            const seatsWrapper = document.createElement("div");
            seatsWrapper.className = "seats-row-items";

            const rowSeats = rows[rowLabel].sort((a, b) => a.seat_number - b.seat_number);

            rowSeats.forEach(seat => {
                const seatElem = document.createElement("div");
                seatElem.className = `seat ${seat.status.toLowerCase()}`;
                seatElem.dataset.seatId = seat.seat_id;
                seatElem.dataset.label = `${seat.row_label}${seat.seat_number}`;
                seatElem.dataset.type = seat.seat_type;
                seatElem.dataset.status = seat.status;
                seatElem.textContent = seat.seat_number;

                // Restore previously selected state if still available or locked by me
                if (selectedSeats.has(seat.seat_id) && (seat.status === "AVAILABLE" || seat.status === "LOCKED_BY_ME")) {
                    seatElem.className = "seat selected";
                }

                // Attach click handler for available/selectable seats
                if (seat.status === "AVAILABLE" || seat.status === "LOCKED_BY_ME") {
                    seatElem.addEventListener("click", () => toggleSeat(seatElem, seat));
                } else if (seat.status === "LOCKED") {
                    seatElem.title = "Temporarily locked by another user";
                } else if (seat.status === "BOOKED") {
                    seatElem.title = "Already booked";
                }

                seatsWrapper.appendChild(seatElem);
            });

            rowElem.appendChild(seatsWrapper);
            seatGrid.appendChild(rowElem);
        });

        updateSummary();
    }

    // 3. Toggle seat selection
    function toggleSeat(seatElem, seat) {
        const seatId = seat.seat_id;
        const seatLabel = `${seat.row_label}${seat.seat_number}`;

        if (selectedSeats.has(seatId)) {
            selectedSeats.delete(seatId);
            seatElem.className = "seat available";
        } else {
            // Max selection limit per booking (e.g., 6 seats)
            if (selectedSeats.size >= 8) {
                showMessage("You can select a maximum of 8 seats per booking.", "warning");
                return;
            }
            selectedSeats.set(seatId, {
                id: seatId,
                label: seatLabel,
                type: seat.seat_type
            });
            seatElem.className = "seat selected";
        }

        updateSummary();
    }

    // 4. Update seat count and price UI
    function updateSummary() {
        const count = selectedSeats.size;
        if (count === 0) {
            selectedSeatsText.textContent = "None";
            totalPriceText.textContent = "₹0.00";
            proceedBtn.disabled = true;
            proceedBtn.classList.add("disabled");
        } else {
            const labels = Array.from(selectedSeats.values()).map(s => s.label).join(", ");
            const total = (count * ticketPrice).toFixed(2);
            selectedSeatsText.textContent = `${labels} (${count} seat${count > 1 ? 's' : ''})`;
            totalPriceText.textContent = `₹${total}`;
            proceedBtn.disabled = false;
            proceedBtn.classList.remove("disabled");
        }
    }

    // 5. Lock seats and proceed to summary
    proceedBtn.addEventListener("click", async function () {
        if (selectedSeats.size === 0) {
            showMessage("Please select at least one seat.", "warning");
            return;
        }

        const seatIds = Array.from(selectedSeats.keys());
        proceedBtn.disabled = true;
        proceedBtn.textContent = "Locking seats...";

        try {
            const res = await fetch("/api/lock-seats", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    show_id: parseInt(showId),
                    seat_ids: seatIds
                })
            });

            const data = await res.json();

            if (res.status === 401) {
                // Not logged in
                window.location.href = `/login?next=/show/${showId}/seats`;
                return;
            }

            if (!data.success) {
                showMessage(data.error || "Unable to lock seats. Please try again.", "danger");
                proceedBtn.disabled = false;
                proceedBtn.textContent = "Proceed to Booking";
                // Reload seats to reflect the conflicting lock/booking immediately
                await loadSeats();
                return;
            }

            // Seats successfully locked in database
            // Redirect to booking summary
            window.location.href = `/booking/summary?show_id=${showId}&seat_ids=${seatIds.join(",")}`;

        } catch (err) {
            console.error("Lock error:", err);
            showMessage("A network error occurred while locking seats. Please try again.", "danger");
            proceedBtn.disabled = false;
            proceedBtn.textContent = "Proceed to Booking";
        }
    });

    // Initial load
    loadSeats();
});
