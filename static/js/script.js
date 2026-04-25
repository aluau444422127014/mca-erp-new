let startX = 0;

document.addEventListener("touchstart", function(e) {
    startX = e.touches[0].clientX;
});

document.addEventListener("touchend", function(e) {
    let endX = e.changedTouches[0].clientX;

    if (startX - endX > 50) {
        showStudent(); // swipe left
    } else if (endX - startX > 50) {
        showStaff(); // swipe right
    }
});

function showStaff() {
    document.getElementById("staffForm").classList.add("active");
    document.getElementById("studentForm").classList.remove("active");
}

function showStudent() {
    document.getElementById("studentForm").classList.add("active");
    document.getElementById("staffForm").classList.remove("active");
}

window.onload = showStaff;
function toggleForm(){
    let form = document.getElementById("formBox");

    if(form.style.display === "none" || form.style.display === ""){
        form.style.display = "block";
    } else {
        form.style.display = "none";
    }
}